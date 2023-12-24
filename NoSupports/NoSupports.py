import adsk.core, adsk.fusion, adsk.cam, traceback
import math

# Globals
_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)
_units = ''
_uiName = 'NoSupports'

# Command inputs


_margin = adsk.core.ValueCommandInput.cast(None)
_width = adsk.core.ValueCommandInput.cast(None)
_height = adsk.core.ValueCommandInput.cast(None)
_hexWidth = adsk.core.ValueCommandInput.cast(None)
_hexSpacing  = adsk.core.ValueCommandInput.cast(None)
_errMessage = adsk.core.TextBoxCommandInput.cast(None)



_module = adsk.core.ValueCommandInput.cast(None)
_imgInputEnglish = adsk.core.ImageCommandInput.cast(None)
_imgInputMetric = adsk.core.ImageCommandInput.cast(None)
_handlers = []

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        cmdDef = _ui.commandDefinitions.itemById('adskNoSupportsPythonScript')
        if not cmdDef:
            # Create a command definition.
            cmdDef = _ui.commandDefinitions.addButtonDefinition('adskNoSupportsPythonScript', 'No supports', 'Creates self supporting structure', 'resources/NoSupports') 
        
        # Connect to the command created event.
        onCommandCreated = MeshCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)
        
        # Execute the command.
        cmdDef.execute()

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class MeshCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Verfies that a value command input has a valid expression and returns the 
# value if it does.  Otherwise it returns False.  This works around a 
# problem where when you get the value from a ValueCommandInput it causes the
# current expression to be evaluated and updates the display.  Some new functionality
# is being added in the future to the ValueCommandInput object that will make 
# this easier and should make this function obsolete.
def getCommandInputValue(commandInput, unitType):
    try:
        valCommandInput = adsk.core.ValueCommandInput.cast(commandInput)
        if not valCommandInput:
            return (False, 0)

        # Verify that the expression is valid.
        des = adsk.fusion.Design.cast(_app.activeProduct)
        unitsMgr = des.unitsManager
        
        if unitsMgr.isValidExpression(valCommandInput.expression, unitType):
            value = unitsMgr.evaluateExpression(valCommandInput.expression, unitType)
            return (True, value)
        else:
            return (False, 0)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the commandCreated event.
class MeshCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            
            # Verify that a Fusion design is active.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            if not des:
                _ui.messageBox('A Fusion design must be active when invoking this command.')
                return()
                
            defaultUnits = des.unitsManager.defaultLengthUnits
                
            # Determine whether to use inches or millimeters as the intial default.
            global _units
            _units = 'mm'
            
            margin = '10'
            marginAttrib = des.attributes.itemByName(_uiName, 'margin')
            if marginAttrib:
                margin = marginAttrib.value

            width = '200'
            widthAttrib = des.attributes.itemByName(_uiName, 'width')
            if widthAttrib:
                width = widthAttrib.value

            height = '100'
            heightAttrib = des.attributes.itemByName(_uiName, 'height')
            if heightAttrib:
                height = heightAttrib.value

            hexWidth = '20'
            hexWidthAttrib = des.attributes.itemByName(_uiName, 'hexWidth')
            if hexWidthAttrib:
                hexWidth = hexWidthAttrib.value

            hexSpacing = '2'
            hexSpacingAttrib = des.attributes.itemByName(_uiName, 'hexSpacing')
            if hexSpacingAttrib:
                hexSpacing = hexSpacingAttrib.value

            cmd = eventArgs.command
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs
            
            global _margin, _width, _height, _hexWidth, _hexSpacing, _module, _errMessage

            # Define the command dialog.         
            _margin = inputs.addStringValueInput('margin', 'Margin', margin)   
            _width = inputs.addStringValueInput('width', 'Width', width)   
            _height = inputs.addStringValueInput('height', 'Height', height)   
            _hexWidth = inputs.addStringValueInput('hexWidth', 'Hex Width', hexWidth)   
            _hexSpacing = inputs.addStringValueInput('hexSpacing', 'hexSpacing', hexSpacing)   

            
            _errMessage = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
            _errMessage.isFullWidth = True
            
            # Connect to the command related events.
            onExecute = MeshCommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)        
            
            onInputChanged = MeshCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)     
            
            onValidateInputs = MeshCommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

            onDestroy = MeshCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def convertUnits(val):
    global _units

    if _units == 'mm':
        return val / 10.0
    elif _units == 'in':
        return val / 25.4
    else:
        return val
    
# Event handler for the execute event.
class MeshCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
  
            # Save the current values as attributes.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            attribs = des.attributes
            attribs.add(_uiName, 'margin',  str(_margin.value))
            attribs.add(_uiName, 'width', str(_width.value))
            attribs.add(_uiName, 'height', str(_height.value))
            attribs.add(_uiName, 'hexWidth', str(_hexWidth.value))
            attribs.add(_uiName, 'hexSpacing', str(_hexSpacing.value))

            margin = convertUnits(float(_margin.value))
            width = convertUnits(float(_width.value))
            height = convertUnits(float(_height.value))
            hexWidth = convertUnits(float(_hexWidth.value))
            hexSpacing = convertUnits(float(_hexSpacing.value))

            # Create the mesh.
            meshComp = drawMesh(des, width, height, hexWidth, hexSpacing, margin)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
                
# Event handler for the inputChanged event.
class MeshCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            changedInput = eventArgs.input
            
            global _units
            _units = 'mm'

            _margin.value = _margin.value
            _margin.unitType = _units
            _width.value = _width.value
            _width.unitType = _units
            _height.value = _height.value
            _height.unitType = _units
            _hexWidth.value = _hexWidth.value
            _hexWidth.unitType = _units
            _hexSpacing.value = _hexSpacing.value
            _hexSpacing.unitType = _units
                                  
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
        
# Event handler for the validateInputs event.
class MeshCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
            
            _errMessage.text = ''
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

import traceback
import adsk.core as core
import adsk.fusion as fusion


def create_clone_sketch_and_geom(
        sktEntity: fusion.SketchEntity
) -> fusion.Sketch:

    skt: fusion.Sketch = None
    if sktEntity.classType() == fusion.Sketch.classType():
        skt = sktEntity
    else:
        skt = sktEntity.parentSketch

    comp: fusion.Component = skt.parentComponent
    refPlane = skt.referencePlane

    # get sketch entities
    sktEnts: core.ObjectCollection = core.ObjectCollection.createWithArray(
        list(skt.sketchCurves),
    )
    [sktEnts.add(pnt) for pnt in skt.sketchPoints]

    # create offset plane
    planes: fusion.ConstructionPlanes = comp.constructionPlanes
    planeIpt: fusion.ConstructionPlaneInput = planes.createInput()
    planeIpt.setByOffset(
        refPlane,
        core.ValueInput.createByReal(0),
    )
    offsetPlane: fusion.ConstructionPlane = planes.add(planeIpt)

    # create sketch
    cloneSkt: fusion.Sketch = comp.sketches.add(offsetPlane)

    # copy
    cloneSkt.copy(
        sktEnts,
        core.Matrix3D.create(),
    )

    return cloneSkt

def create_clone_sketch(
        sktEntity: fusion.SketchEntity
) -> fusion.Sketch:

    skt: fusion.Sketch = None
    if sktEntity.classType() == fusion.Sketch.classType():
        skt = sktEntity
    else:
        skt = sktEntity.parentSketch

    comp: fusion.Component = skt.parentComponent
    refPlane = skt.referencePlane

    # get sketch entities
    sktEnts: core.ObjectCollection = core.ObjectCollection.createWithArray(
        list(skt.sketchCurves),
    )
    #[sktEnts.add(pnt) for pnt in skt.sketchPoints]

    # create offset plane
    planes: fusion.ConstructionPlanes = comp.constructionPlanes
    planeIpt: fusion.ConstructionPlaneInput = planes.createInput()
    planeIpt.setByOffset(
        refPlane,
        core.ValueInput.createByReal(0),
    )
    offsetPlane: fusion.ConstructionPlane = planes.add(planeIpt)

    # create sketch
    cloneSkt: fusion.Sketch = comp.sketches.add(offsetPlane)

    # copy
    #cloneSkt.copy(
    #    sktEnts,
    #    core.Matrix3D.create(),
    #)

    return cloneSkt


def select_ent(
        msg: str,
        filterStr: str
) -> core.Selection:

    try:
        app: core.Application = core.Application.get()
        ui: core.UserInterface = app.userInterface
        sel = ui.selectEntity(msg, filterStr)
        return sel
    except:
        return None

def drawBox(sketch,x,y,w,h):
    lines = sketch.sketchCurves.sketchLines
    x2 = x+w
    y2 = y+h

    blc = adsk.core.Point3D.create(x,y,0.0)
    trc = adsk.core.Point3D.create(x2,y2,0.0)
    recLines = lines.addTwoPointRectangle(blc,trc)

    sketch.geometricConstraints.addHorizontal(recLines.item(0))
    sketch.geometricConstraints.addHorizontal(recLines.item(2))
    sketch.geometricConstraints.addVertical(recLines.item(1))
    sketch.geometricConstraints.addVertical(recLines.item(3))

    dim1 = adsk.core.Point3D.create(x2, y, 0)
    
    sketch.sketchDimensions.addDistanceDimension(recLines.item(0).startSketchPoint, recLines.item(0).endSketchPoint,
                                                 adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                                                 dim1)

    dim2 = adsk.core.Point3D.create(x, y2, 0)
    sketch.sketchDimensions.addDistanceDimension(recLines.item(1).startSketchPoint, recLines.item(1).endSketchPoint,
                                                 adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
                                                 dim2)

def lineMidpoint(line):
    start = line.startSketchPoint.geometry
    end = line.endSketchPoint.geometry
    return adsk.core.Point3D.create((start.x + end.x) / 2.0, (start.y + end.y) / 2.0, (start.z + end.z) / 2.0 )

def drawMidpointConstraint(sketch,outerLine, innerLine,isVertical):
    outerMid = lineMidpoint(outerLine)
    innerMid = lineMidpoint(innerLine)

    newline = sketch.sketchCurves.sketchLines.addByTwoPoints(outerMid,innerMid)
    newline.isConstruction = True

    if isVertical:
        sketch.geometricConstraints.addVertical(newline)
    else:
        sketch.geometricConstraints.addHorizontal(newline)

    sketch.geometricConstraints.addMidPoint(newline.startSketchPoint,outerLine)
    sketch.geometricConstraints.addMidPoint(newline.endSketchPoint,innerLine)

def drawHex(sketch, hexWidth,startX,startY):
    
    apexHeight = hexWidth/2.0

    # overall height of hex is hexWidth*2
    # 1/2 hexWidth for bottom triangle
    # 1/2 hexWidth for top triangle
    # 1 hexWidth for middle square
    
    halfHex = hexWidth/2.0
    #  y coords
    y0 = startY
    y1 = y0 + halfHex
    y2 = y1 + hexWidth
    y3 = y2 + halfHex
    
    # compute x coords
    x0 = startX
    x1 = x0 + halfHex
    x2 = x1 + halfHex

    # compute points: start at bottom apex, work clockwise around perimeter
    p0 = adsk.core.Point3D.create(x1,y0,0.0)
    p1 = adsk.core.Point3D.create(x0,y1,0.0)
    p2 = adsk.core.Point3D.create(x0,y2,0.0)
    p3 = adsk.core.Point3D.create(x1,y3,0.0)
    p4 = adsk.core.Point3D.create(x2,y2,0.0)
    p5 = adsk.core.Point3D.create(x2,y1,0.0)

    # add lines, going clockwise around perimeter
    # bottom apex to first vertical
    l0 = sketch.sketchCurves.sketchLines.addByTwoPoints(p0,p1)

    # first vertical
    l1 = sketch.sketchCurves.sketchLines.addByTwoPoints(p1,p2)
    sketch.geometricConstraints.addVertical(l1)

    # first vert to top apex
    l2 = sketch.sketchCurves.sketchLines.addByTwoPoints(p2,p3)

    # top apex to second vert
    l3 = sketch.sketchCurves.sketchLines.addByTwoPoints(p3,p4)

    # second vertical
    l4 = sketch.sketchCurves.sketchLines.addByTwoPoints(p4,p5)
    sketch.geometricConstraints.addVertical(l4)

    # second vert to bottom apex
    l5 = sketch.sketchCurves.sketchLines.addByTwoPoints(p5,p0)

    # force all points to be connected
    sketch.geometricConstraints.addCoincident(l0.endSketchPoint,l1.startSketchPoint)
    sketch.geometricConstraints.addCoincident(l1.endSketchPoint,l2.startSketchPoint)
    sketch.geometricConstraints.addCoincident(l2.endSketchPoint,l3.startSketchPoint)
    sketch.geometricConstraints.addCoincident(l3.endSketchPoint,l4.startSketchPoint)
    sketch.geometricConstraints.addCoincident(l4.endSketchPoint,l5.startSketchPoint)
    sketch.geometricConstraints.addCoincident(l5.endSketchPoint,l0.startSketchPoint)

    # force apexes to be square
    sketch.geometricConstraints.addPerpendicular(l0,l5)
    sketch.geometricConstraints.addPerpendicular(l2,l3)

    # Add construction line across top of box
    c0 = sketch.sketchCurves.sketchLines.addByTwoPoints(p2,p4)
    c0.isConstruction = True
    sketch.geometricConstraints.addHorizontal(c0)
    sketch.geometricConstraints.addCoincident(c0.startSketchPoint,l2.startSketchPoint)
    sketch.geometricConstraints.addCoincident(c0.endSketchPoint,l3.endSketchPoint)

    # Add construction line from apex to c0 mid
    c0Mid = lineMidpoint(c0)
    c0MidLine = sketch.sketchCurves.sketchLines.addByTwoPoints(c0Mid,p3)
    c0MidLine.isConstruction = True
    sketch.geometricConstraints.addCoincident(c0MidLine.endSketchPoint,l2.endSketchPoint)
    sketch.geometricConstraints.addMidPoint(c0MidLine.startSketchPoint,c0)
    sketch.geometricConstraints.addVertical(c0MidLine)

    # Add construction line across top of box
    c1 = sketch.sketchCurves.sketchLines.addByTwoPoints(p1,p5)
    c1.isConstruction = True
    sketch.geometricConstraints.addHorizontal(c1)
    sketch.geometricConstraints.addCoincident(c1.startSketchPoint,l1.startSketchPoint)
    sketch.geometricConstraints.addCoincident(c1.endSketchPoint,l4.endSketchPoint)

    # Add construction line from bottom apex to c1 mid
    c1Mid = lineMidpoint(c1)
    c1MidLine = sketch.sketchCurves.sketchLines.addByTwoPoints(c1Mid,p0)
    c1MidLine.isConstruction = True
    sketch.geometricConstraints.addCoincident(c1MidLine.endSketchPoint,l5.endSketchPoint)
    sketch.geometricConstraints.addMidPoint(c1MidLine.startSketchPoint,c1)
    sketch.geometricConstraints.addVertical(c1MidLine)

    # constrain box height by constraining first vertical
    sketch.sketchDimensions.addDistanceDimension(l1.startSketchPoint, l1.endSketchPoint,
                                                 adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
                                                 adsk.core.Point3D.create(0, hexWidth, 0))
    # constrain box width by constraining c0
    sketch.sketchDimensions.addDistanceDimension(c0.startSketchPoint, c0.endSketchPoint,
                                                 adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                                                 adsk.core.Point3D.create(hexWidth, 0, 0))


def drawConstrainedFrame(sketch,outerX1,outerY1,outerX2,outerY2,margin):
    
    startItem = sketch.sketchCurves.sketchLines.count
    drawBox(sketch,outerX1,outerY1,outerX2,outerY2)
    innerX1 = outerX1 + margin
    innerY1 = outerY1 + margin
    innerX2 = outerX2 - margin*2.0
    innerY2 = outerY2 - margin*2.0
    drawBox(sketch,innerX1,innerY1,innerX2,innerY2)
        
    outerRectBottom = sketch.sketchCurves.sketchLines.item(startItem)
    innerRectBottom = sketch.sketchCurves.sketchLines.item(startItem+4)
    drawMidpointConstraint(sketch,outerRectBottom,innerRectBottom,True)

    outerRectLeft = sketch.sketchCurves.sketchLines.item(startItem+3)
    innerRectLeft = sketch.sketchCurves.sketchLines.item(startItem+7)
    drawMidpointConstraint(sketch,outerRectLeft,innerRectLeft,False)

def drawMesh(design, width, height, hexWidth, hexSpacing, margin):
    try:
        # Create a new sketch.
        thisComp = design.rootComponent
        sketches = thisComp.sketches


        skt: fusion.Sketch = None
        skt = sketches.item(0)
        if skt.classType() == fusion.Sketch.classType():
            masterSketch = skt
        else:
            masterSketch = skt.parentSketch

        try:
            sketch = create_clone_sketch(masterSketch)
        except Exception as error:
            sketch.name = "Error"

        bbox = masterSketch.boundingBox
        blc = bbox.minPoint
        trc = bbox.maxPoint
        

        # Get the size from the UI
        outerX1 = 0.0
        outerY1 = 0.0
        outerX2 = width
        outerY2 = height

        # Get the size from the componenet
        #outerX1 = blc.x
        #outerY1 = blc.y
        #outerX2 = trc.x
        #outerY2 = trc.y

        # Get the size from the componenet v2
        #outerX1 = 0
        #outerY1 = 0
        #outerX2 = trc.x-blc.x
        #outerY2 = trc.y-blc.y


        drawConstrainedFrame(sketch,outerX1,outerY1,outerX2,outerY2,margin)

        #numRows = computeRows(blc,trc,hexWidth)
        # numCols = computeCols(blc,trc,hexWidth)

        # drawHex(sketch,hexWidth,margin+1.0,margin+1.0)

        sketch.name = 'NoSupports Test'
        return sketch
    
    except Exception as error:
        _ui.messageBox("drawMesh Failed : " + str(error)) 
        return None