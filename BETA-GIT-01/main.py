from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenImage import OnscreenImage
import random

from panda3d.core import loadPrcFile, DirectionalLight, AmbientLight, TransparencyAttrib, WindowProperties, ClockObject, CollisionTraverser, CollisionNode, CollisionBox, CollisionRay, CollisionHandlerQueue, Point3

loadPrcFile('settings.prc')
globalClock = ClockObject.getGlobalClock()


def degToRad(degrees):
    return degrees * (pi / 180.0)

def titulos():
    lista = ['Minepy: no virus attached!', 'Minepy: why are you reading this?', 'Minepy: built with Panda3D!!', 'Minepy: more than a game: a shitty game', 'Minepy: is not awnsering']
    return lista[random.randint(0, 4)]
class Minecraft(ShowBase):

    def __init__(self):

        # VOAR E CAIR
        self.flyingMode = True
        self.gravidade = 10 # Os dois se relacionam
        self.z_moviment = 0

        ShowBase.__init__(self)

        # Create properties and set the title
        winProps = WindowProperties()
        name = titulos()
        winProps.setTitle(name)
        
        # Apply properties to the main window
        self.win.requestProperties(winProps)


        self.selectBlockType = 'dirt'

        self.loadModels()
        self.setupLights()
        self.generateTerrain()
        self.setupCamera()
        self.setupSkybox()
        self.captureMouse()
        self.setupControls()

        self.taskMgr.add(self.update, 'update')


    def update(self, task):
        dt = globalClock.getDt()

        if not self.flyingMode:
            self.z_moviment -= self.gravidade * dt

        playerMovementSpeed = 10
        x_moviment = 0
        y_moviment = 0

        if self.keyMap['running']:
            playerMovementSpeed = 20
        else:
            playerMovementSpeed = 10

        if self.keyMap['forward']:
            x_moviment -= dt * playerMovementSpeed * sin(degToRad(self.camera.getH()))
            y_moviment += dt * playerMovementSpeed * cos(degToRad(self.camera.getH()))

        if self.keyMap['backward']:
            x_moviment += dt * playerMovementSpeed * sin(degToRad(self.camera.getH()))
            y_moviment -= dt * playerMovementSpeed * cos(degToRad(self.camera.getH()))

        if self.keyMap['left']:
            x_moviment -= dt * playerMovementSpeed * cos(degToRad(self.camera.getH()))
            y_moviment -= dt * playerMovementSpeed * sin(degToRad(self.camera.getH()))

        if self.keyMap['right']:
            x_moviment += dt * playerMovementSpeed * cos(degToRad(self.camera.getH()))
            y_moviment += dt * playerMovementSpeed * sin(degToRad(self.camera.getH()))

        if self.keyMap['up'] and self.flyingMode:
            self.z_moviment = playerMovementSpeed

        elif self.keyMap['down'] and self.flyingMode:
            self.z_moviment = -playerMovementSpeed

        elif self.flyingMode:
            self.z_moviment = 0

            
        self.camera.setPos(
            self.camera.getX() + x_moviment,
            self.camera.getY() + y_moviment,
            self.camera.getZ() + self.z_moviment * dt
        )

        if self.cameraSwingActivated:
            md = self.win.getPointer(0)
            mouseX = md.getX()
            mouseY = md.getY()

            mouseChangeX = mouseX - self.lastMouseX
            mouseChangeY = mouseY - self.lastMouseY

            self.cameraSwingFactor = 20

            currentH = self.camera.getH()
            currentP = self.camera.getP()

            self.camera.setHpr(
                currentH - mouseChangeX * dt * self.cameraSwingFactor,
                min(90, max(-90, currentP - mouseChangeY * dt * self.cameraSwingFactor)),
                0
            )

            self.lastMouseX = mouseX
            self.lastMouseY = mouseY

        return task.cont

    def updateKeyMap(self, key, value):
        self.keyMap[key] = value

    def SelectBlockType(self, type):
        self.selectedBlockType = type

    def captureMouse(self):
        self.cameraSwingActivated = True

        md = self.win.getPointer(0)
        self.lastMouseX = md.getX()
        self.lastMouseY = md.getY()

        properties = WindowProperties()
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(properties)

    def releaseMouse(self):
        self.cameraSwingActivated = False

        properties = WindowProperties()
        properties.setCursorHidden(False)
        properties.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(properties)

    def leftClick(self):
        self.captureMouse()
        self.removeBlock()

    def loadModels(self):
        self.dirtBlock = self.loader.loadModel('dirt-block.glb')
        self.sandBlock = self.loader.loadModel('sand-block.glb')
        self.andesiteBlock = self.loader.loadModel('andesite-block.glb')
        self.grassBlock = self.loader.loadModel('grass-block.glb')
        self.stoneBlock = self.loader.loadModel('stone-block.glb')
        self.magmaBlock = self.loader.loadModel('magma-block.glb')
        self.magmaBlock.setScale(2)
        self.obsidianBlock = self.loader.loadModel('obsidian-block.glb')
        self.obsidianBlock.setScale(1.5)

    def removeBlock(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)

            hitNodePath = rayHit.getIntoNodePath()
            hitObject = hitNodePath.getPythonTag('owner')
            distanceFromPlayer = hitObject.getDistance(self.camera)

            if distanceFromPlayer < 12:
                hitNodePath.clearPythonTag('owner')
                hitObject.removeNode()
            

    def createNewBlock(self, x, y, z, type):
        newBlockNode = self.render.attachNewNode('new-block-placeholder')
        newBlockNode.setPos(x, y, z)

        if type == 'dirt':
            self.dirtBlock.instanceTo(newBlockNode)
        elif type == 'sand':
            self.sandBlock.instanceTo(newBlockNode)
        elif type == 'andesite':
            self.andesiteBlock.instanceTo(newBlockNode)
        elif type == 'stone':
            self.stoneBlock.instanceTo(newBlockNode)
        elif type == 'obsidian':
            self.obsidianBlock.instanceTo(newBlockNode)
        elif type == 'grass':
            self.grassBlock.instanceTo(newBlockNode)
        elif type == 'magma':
            self.magmaBlock.instanceTo(newBlockNode)

        blockSolid = CollisionBox((-1, -1, -1), (1, 1, 1))
        blockNode = CollisionNode('block-collision-node')
        blockNode.addSolid(blockSolid)
        collider = newBlockNode.attachNewNode(blockNode)
        collider.setPythonTag('owner', newBlockNode)
        
    def placeBlock(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            hitNodePath = rayHit.getIntoNodePath()
            normal = rayHit.getSurfaceNormal(hitNodePath)
            hitObject = hitNodePath.getPythonTag('owner')
            distanceFromPlayer = hitObject.getDistance(self.camera)

            if distanceFromPlayer < 14:
                hitBlockPos = hitObject.getPos()
                newBlockPos = hitBlockPos + normal * 2
                self.createNewBlock(newBlockPos.x, newBlockPos.y, newBlockPos.z, self.selectBlockType)

    def setupControls(self):
        self.keyMap = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "up": False,
            "down": False,
            "running": False
        }

        self.accept('escape', self.releaseMouse)
        self.accept('mouse1', self.leftClick)
        self.accept('mouse3', self.placeBlock)
        self.accept('1', self.SelectBlockType, ['dirt'])
        self.accept('2', self.SelectBlockType, ['sand'])
        self.accept('3', self.SelectBlockType, ['andesite'])

        self.accept('r', self.updateKeyMap, ['running', True])
        self.accept('r-up', self.updateKeyMap, ['running', False])

        self.accept('w', self.updateKeyMap, ['forward', True])
        self.accept('w-up', self.updateKeyMap, ['forward', False])

        self.accept('a', self.updateKeyMap, ['left', True])
        self.accept('a-up', self.updateKeyMap, ['left', False])

        self.accept('d', self.updateKeyMap, ['right', True])
        self.accept('d-up', self.updateKeyMap, ['right', False])

        self.accept('space', self.updateKeyMap, ['up', True])
        self.accept('space-up', self.updateKeyMap, ['up', False])

        self.accept('s', self.updateKeyMap, ['backward', True])
        self.accept('s-up', self.updateKeyMap, ['backward', False])


        self.accept('lshift', self.updateKeyMap, ['down', True])
        self.accept('lshift-up', self.updateKeyMap, ['down', False])

        self.accept('p', self.toggleFly)

        self.accept('1', self.updateKeyMap, ['grass', True])
        self.accept('2', self.updateKeyMap, ['dirt', True])
        self.accept('3', self.updateKeyMap, ['sand', True])
        self.accept('4', self.updateKeyMap, ['andesite', True])
        self.accept('5', self.updateKeyMap, ['stone', True])
        self.accept('6', self.updateKeyMap, ['magma', True])
        self.accept('7', self.updateKeyMap, ['obsidian', True])
        self.accept('8', self.updateKeyMap, ['andesite', True])
        self.accept('9', self.updateKeyMap, ['andesite', True])
        
    def toggleFly(self):
        self.flyingMode = not self.flyingMode

        if not self.flyingMode:
            self.z_moviment = 0

    def setupCamera(self):
        self.disable_mouse()
        self.camera.setPos(0,0,3)
        self.camLens.setFov(80)

        crosshair = OnscreenImage(
            image = 'crosshairs.png',
            pos = (0,0,0),
            scale = 0.04,
        )
        crosshair.setTransparency(TransparencyAttrib.MAlpha)

        self.cTrav = CollisionTraverser()
        ray = CollisionRay()
        ray.setFromLens(self.camNode, (0, 0))
        rayNode = CollisionNode('line-of-sight')
        rayNode.addSolid(ray)
        rayNodePath = self.camera.attachNewNode(rayNode)
        self.rayQueue = CollisionHandlerQueue()
        self.cTrav.addCollider(rayNodePath, self.rayQueue)

    def setupSkybox(self):
        skybox = self.loader.loadModel('skybox/skybox.egg')
        skybox.setScale(500)
        skybox.setBin('background', 1)
        skybox.setDepthWrite(0)
        skybox.setLightOff()
        skybox.reparentTo(self.render)

    def generateTerrain(self):
        for z in range(20):
            for y in range(20):
                for x in range(20):
                    self.createNewBlock(
                        x * 2 - 20,
                        y * 2 - 20,
                        -z * 2,
                        'grass' if z == 0 else 'dirt' if z < 5 else 'sand' if z < 8 else 'andesite' if z == 8 else 'stone' if z < 17 else 'magma' if z < 19 else 'obsidian'
                    )

    def setupLights(self):
        mainLight = DirectionalLight('main light')
        mainLightNodePath = self.render.attachNewNode(mainLight)
        mainLightNodePath.setHpr(30, -60, 0)
        self.render.setLight(mainLightNodePath)

        ambientLight = AmbientLight('ambient light')
        ambientLight.setColor((0.3, 0.3, 0.3, 1))
        ambientLightNodePath = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNodePath)

game = Minecraft()
game.run()