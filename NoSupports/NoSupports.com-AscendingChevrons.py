import adsk.core, adsk.fusion, adsk.cam, traceback
import math

import os, sys
sys.path.append("C:/Python311/Lib/site-packages")

import svg
import ezdxf

# Globals
_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)
_units = ''
_uiName = 'NoSupports.com Ascending Chevron'

class UiLogger:
    def __init__(self, forceUpdate):  
        app = adsk.core.Application.get()
        ui  = app.userInterface
        palettes = ui.palettes
        self.textPalette = palettes.itemById("TextCommands")
        self.forceUpdate = forceUpdate
        self.textPalette.isVisible = True 
    
    def print(self, text):       
        self.textPalette.writeText(text)
        if (self.forceUpdate):
            adsk.doEvents() 

# Command inputs

_sketchName = adsk.core.ValueCommandInput.cast(None)
_marginParam = adsk.core.ValueCommandInput.cast(None)
_widthParam = adsk.core.ValueCommandInput.cast(None)
_heightParam = adsk.core.ValueCommandInput.cast(None)
_numCols = adsk.core.ValueCommandInput.cast(None)
_numRows = adsk.core.ValueCommandInput.cast(None)
_webbing  = adsk.core.ValueCommandInput.cast(None)
_errMessage = adsk.core.TextBoxCommandInput.cast(None)
_module = adsk.core.ValueCommandInput.cast(None)
_handlers = []

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        cmdDef = _ui.commandDefinitions.itemById('adskNoSupportsPythonScript')
        if not cmdDef:
            # Create a command definition.
            cmdDef = _ui.commandDefinitions.addButtonDefinition('adskNoSupportsPythonScript', 'NoSupports.com Ascending Chevrons', 'Creates self supporting structure', 'resources/NoSupports') 
        
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
            
            sketchName = 'Sketch1'
            sketchNameAttrib = des.attributes.itemByName(_uiName, 'sketchName')
            if sketchNameAttrib:
                sketchName = sketchNameAttrib.value

            margin = 'margin'
            marginAttrib = des.attributes.itemByName(_uiName, 'margin')
            if marginAttrib:
                margin = marginAttrib.value

            width = 'w1'
            widthAttrib = des.attributes.itemByName(_uiName, 'width')
            if widthAttrib:
                width = widthAttrib.value

            height = 'h1'
            heightAttrib = des.attributes.itemByName(_uiName, 'height')
            if heightAttrib:
                height = heightAttrib.value

            numCols = '4'
            numColsAttrib = des.attributes.itemByName(_uiName, 'numCols')
            if numColsAttrib:
                numCols = numColsAttrib.value


            numRows = '4'
            numRowsAttrib = des.attributes.itemByName(_uiName, 'numRows')
            if numRowsAttrib:
                numRows = numRowsAttrib.value

            webbing = '2'
            webbingAttrib = des.attributes.itemByName(_uiName, 'webbing')
            if webbingAttrib:
                webbing = webbingAttrib.value

            cmd = eventArgs.command
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs
            
            global _marginParam, _sketchName, _widthParam, _heightParam, _numCols, _numRows, _webbing, _module, _errMessage

            # Define the command dialog.         
            _imgInput = inputs.addImageCommandInput('infoImage', '', 'resources/AscendingChevrons.png')
            _imgInput.isFullWidth = True
            _marginParam = inputs.addStringValueInput('margin', 'Margin', margin)   
            _sketchName = inputs.addStringValueInput('sketchName', 'SketchName', sketchName)   
            _widthParam = inputs.addStringValueInput('width', 'Width', width)   
            _heightParam = inputs.addStringValueInput('height', 'Height', height)   
            _numCols = inputs.addStringValueInput('numCols', 'Num Cols', numCols)   
            _numRows = inputs.addStringValueInput('numRows', 'Num Rows', numRows)   
            _webbing = inputs.addStringValueInput('webbing', 'Webbing', webbing)   

            
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
    

def getDesignParam(design,paramName,convert):
    param = design.allParameters.itemByName(paramName)
    if convert:
        return convertUnits(param.value)
    else:
        return param.value
 
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
            attribs.add(_uiName, 'margin',  str(_marginParam.value))
            attribs.add(_uiName, 'sketchName',  str(_sketchName.value))
            attribs.add(_uiName, 'width', str(_widthParam.value))
            attribs.add(_uiName, 'height', str(_heightParam.value))
            attribs.add(_uiName, 'numCols', str(_numCols.value))
            attribs.add(_uiName, 'numRows', str(_numRows.value))
            attribs.add(_uiName, 'webbing', str(_webbing.value))

            width = getDesignParam(des,str(_widthParam.value),False)
            height = getDesignParam(des,str(_heightParam.value),False)
            margin = getDesignParam(des,str(_marginParam.value),False)
            numCols = float(_numCols.value)
            numRows = float(_numRows.value)
            webbing = convertUnits(float(_webbing.value))
            sketchName = str(_sketchName.value)


            log = UiLogger(True)

            log.print("Width " + str(width))
            log.print("Height " + str(height))
            log.print("Margin " + str(margin))

            # Create the mesh.
            # svgDrawAscendingChevrons(des, width, height, numCols, numRows, webbing, margin,sketchName)
            dxfDrawAscendingChevrons(des, width, height, numCols, numRows, webbing, margin,sketchName)
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

            _marginParam.value = _marginParam.value
            _sketchName.value = _sketchName.value
            _widthParam.value = _widthParam.value
            _widthParam.unitType = _units
            _heightParam.value = _heightParam.value
            _heightParam.unitType = _units
            _numCols.value = _numCols.value
            _numRows.value = _numRows.value
            _webbing.value = _webbing.value
            _webbing.unitType = _units
                                  
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

def drawHex(sketch, numCols,startX,startY):
    
    apexHeight = numCols/2.0

    # overall height of hex is numCols*2
    # 1/2 numCols for bottom triangle
    # 1/2 numCols for top triangle
    # 1 numCols for middle square
    
    halfHex = numCols/2.0
    #  y coords
    y0 = startY
    y1 = y0 + halfHex
    y2 = y1 + numCols
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
                                                 adsk.core.Point3D.create(0, numCols, 0))
    # constrain box width by constraining c0
    sketch.sketchDimensions.addDistanceDimension(c0.startSketchPoint, c0.endSketchPoint,
                                                 adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                                                 adsk.core.Point3D.create(numCols, 0, 0))


# TODO: Add a flip axis flag to script and try to deduce it automatically

def flipY(y,height):
    return y #height-y - height

def svgDrawChevron(sketch, chevronWidth,webbing,startX,startY,height):
    apexHeight = chevronWidth/2.0
    halfWidth = chevronWidth/2.0
    # overall webbing + half width
    # 1/2 numCols for bottom triangle
    # 1/2 numCols for top triangle
    # 1 numCols for middle square
    #  y coords

    y0 = startY
    y1 = y0 + webbing
    y2 = y1 + apexHeight
    y3 = y2 - webbing

    y0 = flipY(y0,height)
    y1 = flipY(y1,height)
    y2 = flipY(y2,height)
    y3 = flipY(y3,height)


    # compute x coords
    x0 = startX
    x1 = x0 + halfWidth
    x2 = startX+chevronWidth

    return svg.Polyline(
                points=[
                    x0, y0, 
                    x0, y1,
                    x1, y2,
                    x2, y1,
                    x2, y0,
                    x1, y3,
                    x0, y0
                ],
                stroke="orange",
                fill="transparent",
                stroke_width=1,
            )

def dxfDrawChevron(msp, chevronWidth,webbing,startX,startY,height):
    apexHeight = chevronWidth/2.0
    halfWidth = chevronWidth/2.0
    # overall webbing + half width
    # 1/2 numCols for bottom triangle
    # 1/2 numCols for top triangle
    # 1 numCols for middle square
    #  y coords

    y0 = startY
    y1 = y0 + webbing
    y2 = y1 + apexHeight
    y3 = y2 - webbing

    y0 = flipY(y0,height)
    y1 = flipY(y1,height)
    y2 = flipY(y2,height)
    y3 = flipY(y3,height)

    # compute x coords
    x0 = startX
    x1 = x0 + halfWidth
    x2 = startX+chevronWidth

    points = [ (x0, y0), (x0, y1), (x1, y2),(x2, y1), (x2, y0),(x1, y3),(x0, y0) ]
                
    msp.add_lwpolyline(points)


def findSketch(sketches,sketchName):

    skt: fusion.Sketch = None

    log = UiLogger(True)

    log.print("Found sketch " + sketchName)

    skt = sketches.itemByName(sketchName)

    if skt.classType() == fusion.Sketch.classType():
        result = skt
    else:
        result = skt.parentSketch

    return result


def svgDrawStrut(sketch,strutHeight,webbing,startX,startY,height):
    # compute y coords
    yAdj = webbing/2.0
    Y0 = startY
    Y1 = Y0 + strutHeight

    Y0 = flipY(Y0,height)
    Y1 = flipY(Y1,height)

    # compute x coords
    X0 = startX - webbing/2.0
    X1 = X0 + webbing

    elements=[
        svg.Line(
            x1=X0, y1=Y0,
            x2=X0, y2=Y1,
            stroke="red",
            stroke_width=1,
        ),
        svg.Line(
            x1=X1, y1=Y0,
            x2=X1, y2=Y1,
            stroke="red",
            stroke_width=1,
        )
    ]

    return elements

def dxfDrawStrut(msp,strutHeight,webbing,startX,startY,height):
    # compute y coords
    yAdj = webbing/2.0
    y0 = startY
    y1 = y0 + strutHeight

    y0 = flipY(y0,height)
    y1 = flipY(y1,height)

    # compute x coords
    x0 = startX - webbing/2.0
    x1 = x0 + webbing

    l1points = [(x0,y0),(x0,y1)]
    msp.add_lwpolyline(l1points)

    l2points = [(x1,y0),(x1,y1)]
    msp.add_lwpolyline(l2points)


def svgDrawAscendingChevrons(design, width, height, numCols, numRows, webbing, margin,sketchName):
    # TODO: Pass the cloned sketch in, fail with gracful error if sketch not found

    # Create a new sketch.
    thisComp = design.rootComponent
    masterSketch: fusion.Sketch = findSketch(thisComp.sketches,sketchName)
    sketch = create_clone_sketch(masterSketch)

    log = UiLogger(True)

    # Get the size from the UI
    outerX1 = 0.0
    outerY1 = 0.0
    outerX2 = width
    outerY2 = height

    # TODO: Switch to a polyline for consistency with chevrons and flipY
    elements = [
        svg.Rect(
                x=0, y=flipY(0,height),
                width=outerX2, height=outerY2,
                stroke="black",
                fill="transparent",
                stroke_width=1,
            ),
            svg.Rect(
                x=margin, y=flipY(margin,height),
                width=width-margin*2, height=(height-margin*2),
                stroke="black",
                fill="transparent",
                stroke_width=1,
            )]

    xOffset = margin
    yOffset = margin

    overallWidth = width-margin*2.0
    overallHeight= height-margin*2.0

    chevronWidth = (overallWidth/numCols)
    
    numCols = int(numCols)
    numRows = int (numRows)

    xStep = chevronWidth
    yStep = overallHeight/float(numRows)

    # TODO: broken when numRows = 1
    if numRows == 1:
        log.print("Uh oh, broken code!")
    yStep = (overallHeight-(chevronWidth/2)-webbing)/(numRows-1)

    xOffset = margin
    for y in range (0,numRows):
        for x in range (0,numCols):
            chevron = svgDrawChevron(sketch,chevronWidth,webbing,xOffset,yOffset,height)
            elements.append(chevron)

            xOffset += xStep
        xOffset = margin
        yOffset += yStep

    # Draw struts at right sides of chevrons, except for last chevron
    xOffset = margin
    yOffset = margin

    strutHeight = yStep*(numRows-1) + webbing/2

    # TODO: Handle case with no struts!
    for x in range (1,numCols):
        struts = svgDrawStrut(sketch,strutHeight,webbing,(xOffset+xStep),yOffset,height)
        elements.append(struts) 
        xOffset += xStep

    canvas = svg.SVG(
        x=outerX1,
        y=outerY1,
        width=100,
        height=100,
        elements = elements
    )

    # TODO: convert to DXF https://ezdxf.mozman.at/docs/tutorials/lwpolyline.html

    #log.print(str(canvas))


    file = open("c:/foo.svg","w")
    with open("c:/foo.svg", 'w') as file:
        file.write(str(canvas))

    sketch.importSVG("c:/foo.svg", 0.0, -height, 37.79528)

    sketch.name = 'NoSupports Test'
    return sketch



def dxfDrawAscendingChevrons(design, width, height, numCols, numRows, webbing, margin,sketchName):
    # TODO: Pass the cloned sketch in, fail with gracful error if sketch not found

    # Create a new sketch.
    thisComp = design.rootComponent
    masterSketch: fusion.Sketch = findSketch(thisComp.sketches,sketchName)
    sketch = create_clone_sketch(masterSketch)

    log = UiLogger(True)

    # Get the size from the UI
    outerX1 = 0.0
    outerY1 = 0.0
    outerX2 = width
    outerY2 = height

    doc = ezdxf.new("R2000")
    msp = doc.modelspace()

    points = [(0, 0), (3, 0), (6, 3), (6, 6)]

    r1x1 = 0
    r1y1 = flipY(0,height)
    r1x2 = outerX2
    r1y2 = flipY(outerY2,height)
    msp.add_lwpolyline([(r1x1,r1y1),(r1x2,r1y1),(r1x2,r1y2),(r1x1,r1y2),(r1x1,r1y1)])


    r2x1 = margin
    r2y1 = flipY(margin,height)
    r2x2 = outerX2-margin
    r2y2 = flipY(outerY2-margin,height)

    msp.add_lwpolyline([(r2x1,r2y1),(r2x2,r2y1),(r2x2,r2y2),(r2x1,r2y2),(r2x1,r2y1)])

    xOffset = margin
    yOffset = margin

    overallWidth = width-margin*2.0
    overallHeight= height-margin*2.0

    chevronWidth = (overallWidth/numCols)
    
    numCols = int(numCols)
    numRows = int (numRows)

    xStep = chevronWidth
    yStep = overallHeight/float(numRows)

    # TODO: broken when numRows = 1
    if numRows == 1:
        log.print("Uh oh, broken code!")
    yStep = (overallHeight-(chevronWidth/2)-webbing)/(numRows-1)

    xOffset = margin
    for y in range (0,numRows):
        for x in range (0,numCols):
            dxfDrawChevron(msp,chevronWidth,webbing,xOffset,yOffset,height)
            xOffset += xStep
        xOffset = margin
        yOffset += yStep

    # Draw struts at right sides of chevrons, except for last chevron
    xOffset = margin
    yOffset = margin

    strutHeight = yStep*(numRows-1) + webbing/2

    # TODO: Handle case with no struts!
    for x in range (1,numCols):
        dxfDrawStrut(msp,strutHeight,webbing,(xOffset+xStep),yOffset,height)
        xOffset += xStep


    doc.saveas("c:/foo.dxf")


    importManager = adsk.core.Application.get().importManager
    dxfOptions = importManager.createDXF2DImportOptions("C:/foo.dxf", thisComp.xZConstructionPlane)

    dxfOptions.isViewFit = False 
    dxfOptions.isSingleSketchResult = True
            
    # Import dxf file to root component
    importManager.importToTarget(dxfOptions, thisComp)

    sketch.name = 'NoSupports Test'
    return sketch


