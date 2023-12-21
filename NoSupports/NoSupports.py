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

def drawBox(sketch,x,y,w,h):
    lines = sketch.sketchCurves.sketchLines
    x2 = x+w
    y2 = y+h
    recLines = lines.addTwoPointRectangle(adsk.core.Point3D.create(x,y,0.0),adsk.core.Point3D.create(x2,y2,0.0))

    sketch.geometricConstraints.addHorizontal(recLines.item(0))
    sketch.geometricConstraints.addHorizontal(recLines.item(2))
    sketch.geometricConstraints.addVertical(recLines.item(1))
    sketch.geometricConstraints.addVertical(recLines.item(3))

    sketch.sketchDimensions.addDistanceDimension(recLines.item(0).startSketchPoint, recLines.item(0).endSketchPoint,
                                                 adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                                                 adsk.core.Point3D.create(x2, y, 0))

    sketch.sketchDimensions.addDistanceDimension(recLines.item(1).startSketchPoint, recLines.item(1).endSketchPoint,
                                                 adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
                                                 adsk.core.Point3D.create(x, y2, 0))

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

def drawMesh(design, width, height, hexWidth, hexSpacing, margin):
    try:
        # Create a new sketch.
        thisComp = design.rootComponent

        sketches = thisComp.sketches
        xyPlane = thisComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        # Draw a circle for the base.
        outerX1 = 0.0
        outerY1 = 0.0
        outerX2 = width
        outerY2 = height
        drawBox(sketch,outerX1,outerY1,outerX2,outerY2)

        innerX1 = outerX1 + margin
        innerY1 = outerX1 + margin
        innerX2 = outerX2 - margin*2.0
        innerY2 = outerY2 - margin*2.0
        drawBox(sketch,innerX1,innerY1,innerX2,innerY2)
        
        outerRectBottom = sketch.sketchCurves.sketchLines.item(0)
        innerRectBottom = sketch.sketchCurves.sketchLines.item(4)
        drawMidpointConstraint(sketch,outerRectBottom,innerRectBottom,True)

        outerRectLeft = sketch.sketchCurves.sketchLines.item(3)
        innerRectLeft = sketch.sketchCurves.sketchLines.item(7)
        drawMidpointConstraint(sketch,outerRectLeft,innerRectLeft,False)

        sketch.name = 'NoSupports Test'
        return sketch
    
    except Exception as error:
        _ui.messageBox("drawMesh Failed : " + str(error)) 
        return None