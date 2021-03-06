import pygame
import random
import noise
#from pyscroll import pyscroll
import pyscroll
import sys

pygame.init()

try:
    import android
    android.init()
    from jnius import autoclass
except ImportError:
    android = None

if android:
    android.map_key(android.KEYCODE_BACK, pygame.K_ESCAPE)
    android.map_key(android.KEYCODE_BUTTON_A, pygame.K_x)
    android.map_key(android.KEYCODE_BUTTON_B, pygame.K_c)
    android.map_key(android.KEYCODE_MENU, pygame.K_F1)

    OuyaController=autoclass('tv.ouya.console.api.OuyaController')
    Facade=autoclass('tv.ouya.console.api.OuyaFacade')
    facade=Facade.getInstance()

try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer

#screen=pygame.display.set_mode((0,0),pygame.DOUBLEBUF|pygame.FULLSCREEN)
screen=pygame.display.set_mode((800,600),pygame.DOUBLEBUF)

if len(sys.argv)==2 and sys.argv[1]=="--big":
    screen_real=screen
    screen=pygame.Surface((400,300)).convert()

screen_w=screen.get_width()
screen_h=screen.get_height()
TILE=16

pygame.display.flip()

the_font=pygame.font.Font("orbitron-black.ttf", 14)

dwarf=pygame.image.load("gnome.png").convert_alpha()
rec=pygame.image.load("rec.png").convert_alpha()

dirt=pygame.image.load("dirt.png").convert()
hall=pygame.image.load("hall.png").convert()
boletus=pygame.image.load("boletus2.png").convert()
amanita=pygame.image.load("amanita.png").convert()
chicken=pygame.image.load("chicken.png").convert()
grass=pygame.image.load("grass.png").convert()
sky=pygame.image.load("sky.png").convert()
bedrock=pygame.image.load("bedrock.png").convert()
ladder=pygame.image.load("ladder2.png").convert()
iron_ore=pygame.image.load("iron3.png").convert()
bamboo=pygame.image.load("bamboo2.png").convert()
diamond=pygame.image.load("diamond.png").convert()

mini_boletus=pygame.image.load("boletus-mini.png").convert_alpha()
mini_pick=pygame.image.load("pick-mini.png").convert_alpha()
mini_ladder=pygame.image.load("ladder-mini.png").convert_alpha()
mini_hammer=pygame.image.load("hammer-mini.png").convert_alpha()
mini_ladder=pygame.image.load("ladder-mini.png").convert_alpha()
mini_sickle=pygame.image.load("sickle-mini.png").convert_alpha()
iron_bar=pygame.image.load("iron-bar.png").convert_alpha()
wood_bar=pygame.image.load("wood-bar.png").convert_alpha()
mini_diamond=pygame.image.load("diamond-mini.png").convert_alpha()

tiles=[hall,dirt,grass,sky,bedrock,ladder,boletus,amanita,iron_ore,bamboo,diamond]

FALL_SPEED=2

def can_stand(player,ground_coords):
    for x,y in (player.bottomleft,player.bottomright,
                player.midleft, player.midright):
        if ground_coords[(x-1)/TILE][(y-1)/TILE] in [1,4,5,8,10]:
            return True
    return False

def cant_move(player,ground_coords):
    for x,y in (player.bottomleft,player.bottomright):
        if ground_coords[(x-1)/TILE][(y-1)/TILE] in [1,4,8,10]:
            return True
    for x,y in (player.topleft,player.topright,
                player.midleft, player.midright):
        if ground_coords[x/TILE][y/TILE] in [1,4,8,10]:
            return True
    return False

def cant_climb(player,ground_coords):
    x,y=player.midbottom
    ladder=False
    if ground_coords[x/TILE][y/TILE]==5:
        ladder=True

    x,y=player.center
    if ground_coords[x/TILE][y/TILE]==5:
        ladder=True
    
    if ladder:
        return cant_move(player,ground_coords)
    else:
        return True

class Mob(pygame.sprite.Sprite):
    def __init__(self,img,ground,t_d):
       pygame.sprite.Sprite.__init__(self)
       self.t_d=t_d
       self.image = img
       self.image_orig=img
       self.rect = self.image.get_rect()
       self.behaviour=None
       self.terrain=ground
       self.command=None
       self.parameter=None
       self.face=1

    def do_command(self,command):
        if command=="LEFT":
            self.move_collide(-1,0,3,cant_move)
            self.face=1
            return True
        elif command=="RIGHT":
            self.move_collide(1,0,3,cant_move)
            self.face=-1
            return True
        elif command=="UP":
            self.move_collide(0,-1,2,cant_climb)
            return True
        elif command=="DOWN":
            self.move_collide(0,1,2,cant_move)
            return True
        return False
       
    def commands_behave(self,commands):
        while True:
            for c in commands:
                self.do_command(c)
                yield None

    def move_collide(self,dx,dy,n,cant_move):
        for i in range(n):
            x,y=self.rect.center
            self.rect.center=x+dx,y+dy
            if cant_move(self.rect,self.terrain):
                self.rect.center=x,y
                break

    def fall(self):
        self.move_collide(0,1,FALL_SPEED,can_stand)

    def update(self,delta):
        self.fall()

        if self.command is not None:
            self.do_command(self.command)
            self.command=None
            self.behaviour=None
        elif self.behaviour is not None:
            try:
                self.behaviour.next()
            except StopIteration:
                self.behaviour.close
                self.behaviour=None

        self.image=self.image_orig

        if self.inventory is not None:
            self.inventory.rect.center=self.rect.midright

        if self.face==1:
            self.image=pygame.transform.flip(self.image_orig, True, False)
            if self.inventory is not None:
                self.inventory.rect.center=self.rect.midleft

class FoodThing(pygame.sprite.Sprite):
    name="Food"
    def __init__(self,img,pos,health):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.durability=1
        self.img = img
        self.rect = self.image.get_rect()
        self.health=health
        self.rect.midbottom=pos

class RawMaterial(pygame.sprite.Sprite):
    def __init__(self,img,pos,tag):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.durability=1
        self.img = img
        self.rect = self.image.get_rect()
        self.rect.midbottom=pos
        self.tag=tag
        self.name=tag

class Tool(pygame.sprite.Sprite):
    max_dur=1
    def __init__(self,pos=(0,0)):
        self.durability=self.max_dur
        pygame.sprite.Sprite.__init__(self)
        self.image=self.img
        self.rect = self.image.get_rect()
        self.rect.midbottom=pos

    def use_left(self,user):
        return self.use_here(user)
    def use_right(self,user):
        return self.use_here(user)
    def use_up(self,user):
        return self.use_here(user)
    def use_down(self,user):
        return self.use_here(user)
    def use_here(self,user):
        return False

class PickAxe(Tool):
    img=mini_pick
    name="pick"
    max_dur=100
    def pick_block(self,x,y,user):
        if user.terrain[x/TILE][y/TILE]==1:
            self.durability-=1
            user.terrain[x/TILE][y/TILE]=0
            user.t_d.set()
            return True
        elif user.terrain[x/TILE][y/TILE]==8:
            self.durability-=2
            user.terrain[x/TILE][y/TILE]=0
            user.t_d.set()
            for i in range(3):
                t=RawMaterial(iron_bar,user.rect.midbottom,"iron")
                user.worldgroup.add(t)
                user.objects.append(t)
            return True
        elif user.terrain[x/TILE][y/TILE]==10:
            self.durability-=10
            user.terrain[x/TILE][y/TILE]=0
            user.t_d.set()
            t=RawMaterial(mini_diamond,user.rect.midbottom,"diamond")
            user.worldgroup.add(t)
            user.objects.append(t)
            return True

    def use_here(self,user):
        x,y=user.rect.center
        return self.pick_block(x,y,user)
    def use_left(self,user):
        x,y=user.rect.center
        return self.pick_block(x-15,y,user)
    def use_right(self,user):
        x,y=user.rect.center
        return self.pick_block(x+15,y,user)
    def use_up(self,user):
        x,y=user.rect.center
        return self.pick_block(x,y-15,user)
    def use_down(self,user):
        x,y=user.rect.center
        return self.pick_block(x,y+15,user)

class Sickle(Tool):
    img=mini_sickle
    name="sickle"
    max_dur=100

    def pick_block(self,x,y,user):
        if user.terrain[x/TILE][y/TILE]==6:
            self.durability-=1
            user.terrain[x/TILE][y/TILE]=0
            user.t_d.set()
            a,b=user.rect.midbottom
            for i in range(3):
                t=FoodThing(mini_boletus,(a+(i-1)*6,b),10000)
                user.worldgroup.add(t)
                user.objects.append(t)
            return True
        elif user.terrain[x/TILE][y/TILE]==9:
            self.durability-=1
            user.terrain[x/TILE][y/TILE]=0
            user.t_d.set()
            for i in range(3):
                t=RawMaterial(wood_bar,user.rect.midbottom,"wood")
                user.worldgroup.add(t)
                user.objects.append(t)
            return True
            
    def use_here(self,user):
        x,y=user.rect.center
        return self.pick_block(x,y,user)

class Ladder(Tool):
    img=mini_ladder
    name="ladder"
    max_dur=100

    def use_here(self,user):
        x,y=user.rect.center
        if user.terrain[x/TILE][y/TILE]==0:
            self.durability-=1
            user.terrain[x/TILE][y/TILE]=5
            user.t_d.set()
            return True

class Hammer(Tool):
    img=mini_hammer
    name="hammer"
    max_dur=50

    def use_here(self,user):
        x,y=user.rect.center

        objects=[]
        for o in user.objects[:]:
            ox,oy=o.rect.center
            distance=abs(ox-x)+abs(oy-y)
            if distance<32 and isinstance(o,RawMaterial):
                objects.append(o)

        tags=[o.tag for o in objects]
        tags.sort()

        t=None

        if tags==["wood","wood","wood"]:
            t=Ladder(user.rect.midbottom)
        elif tags==["iron","wood","wood"]:
            t=Hammer(user.rect.midbottom)
        elif tags==["iron","iron","wood"]:
            t=PickAxe(user.rect.midbottom)
        elif tags==["iron","wood"]:
            t=Sickle(user.rect.midbottom)

        if t is not None:
            user.worldgroup.add(t)
            user.objects.append(t)
            self.durability-=1
            for o in objects:
                user.objects.remove(o)
                user.worldgroup.remove(o)

class Dwarf(Mob):
    def __init__(self,x,y,terrain,t_d,group,objects):
       Mob.__init__(self,dwarf,terrain,t_d)
       self.rect.center=x,y
       self.startingpoint=x,y
       self.inventory=None
       self.food=10000
       self.worldgroup=group
       self.objects=objects
    
    def do_command(self,command):
        if command is None:
            return False
        x,y=self.rect.center
        if command=="LOOP":
            sx,sy=self.startingpoint
            if abs(sx-x)+abs(sy-y)<10:
                self.rect.center=self.startingpoint
            else:
                self.startingpoint=self.rect.center
            return True
        elif command=="PUT":
            if self.inventory is not None:
                self.inventory.rect.midbottom=self.rect.midbottom
                self.objects.append(self.inventory)
                self.inventory=None
        elif command=="TAKE":
            if self.inventory is None:
                max_d=16
                nearest=None
                for o in self.objects[:]:
                    ox,oy=o.rect.center
                    distance=abs(ox-x)+abs(oy-y)
                    if distance<max_d:
                        nearest=o
                        max_d=distance
                if nearest is not None:
                    self.objects.remove(nearest)
                    self.inventory=nearest
        elif command[:3]=="USE":
            if isinstance(self.inventory,FoodThing):
                self.food+=self.inventory.health
                self.worldgroup.remove(self.inventory)
                self.inventory=None
            if isinstance(self.inventory,Tool):
                if self.food==0:
                    self.behaviour=None
                    self.command=None
                    return False
                if len(command)==3:
                    direction=None
                else:
                    direction=command[4:]
                if direction=="LEFT":
                    return self.inventory.use_left(self)
                elif direction=="RIGHT":
                    return self.inventory.use_right(self)
                elif direction=="UP":
                    return self.inventory.use_up(self)
                elif direction=="DOWN":
                    return self.inventory.use_down(self)
                else:
                    return self.inventory.use_here(self)
        else:
            return Mob.do_command(self,command)

    def try_eat(self):
        max_d=48
        nearest=None
        x,y=self.rect.center
        for o in self.objects[:]:
            ox,oy=o.rect.center
            distance=abs(ox-x)+abs(oy-y)
            if distance<max_d and isinstance(o,FoodThing):
                nearest=o
                max_d=distance
        if nearest is not None:
            self.objects.remove(nearest)
            self.worldgroup.remove(nearest)
            self.food+=nearest.health

    def update(self,delta):
        Mob.update(self,delta)
        if self.food<2000:
            self.try_eat()
        if self.food>0:
            self.food-=1
        if self.inventory:
            if self.inventory.durability<1:
                self.worldgroup.remove(self.inventory)
                self.inventory=None

class TMX(object):
    pass

class TERRAIN_DIRTY(object):
    def __init__(self):
        self.d=False

    def get(self):
        r=self.d
        self.d=False
        return r

    def set(self):
        self.d=True

class MyData(pyscroll.TiledMapData):

    tilewidth  = TILE
    tileheight = TILE
    width  = 1000
    height = 1000
    visible_layers = [0]
    visible_tile_layers=[0]
    visible_object_layers=[]

    def __init__(self,terrain):
        self.terrain=terrain
        self.tmx=TMX()
        self.tmx.map_gid=0        

    def get_tile_image(self, position):
        x,y,layer=position
        return tiles[self.terrain[x][y]]

def make_terrain():
    terrain=[[1-int(abs(noise.pnoise3(i*0.4+0.5,j*0.1+0.5,0.5))*2)
              for i in range(500)] 
             for j in range(5000)]

    for x in range(5000):
        for y in range(50):
            terrain[x][y]=3
        terrain[x][50]=2

    for x in range(100):
        for y in range(500):
            terrain[-x][y]=4
            terrain[x][y]=4

    for x in range(5000):
        for y in range(50,100):
            ri=random.random()
            if terrain[x][y]==0 and terrain[x][y+1]==1:
                if ri<0.05:
                    terrain[x][y]=9
            if terrain[x][y]==0 and terrain[x][y+1]==1:
                if ri<0.2:
                    terrain[x][y]=6
            if terrain[x][y]==1:
                if ri<0.007:
                    terrain[x][y]=8
        for y in range(110,200):
            ri=random.random()
            if terrain[x][y]==1:
                if ri<0.002:
                    terrain[x][y]=10
    return terrain

def make_shadow_terrain():
    terrain=[[1-int(abs(noise.pnoise3(i*0.6+0.5,j*0.2+0.5,0.8))*5)
              for i in range(500)] 
             for j in range(5000)]

    return terrain

def game_loop():
    clock=pygame.time.Clock()
    recording=False
    
    terrain=make_terrain()
    terrain_d=TERRAIN_DIRTY()
    objects=[]

    map_layer = pyscroll.BufferedRenderer(MyData(terrain), (screen_w,screen_h))
    group = pyscroll.PyscrollGroup(map_layer=map_layer)

    macro=[]
    mobs=[]
    dwarves=[]
    dw_index=0

    position=TILE*2500,TILE*50
    
    a_dwarf=Dwarf(2500*16,40*16,terrain,terrain_d,group,objects)
    another_dwarf=Dwarf(2502*16,40*16,terrain,terrain_d,group,objects)
    yet_another_dwarf=Dwarf(2505*16,40*16,terrain,terrain_d,group,objects)
    fourth_dwarf=Dwarf(2507*16,40*16,terrain,terrain_d,group,objects)

    dwarves.append(a_dwarf)
    group.add(a_dwarf)
    dwarves.append(another_dwarf)
    group.add(another_dwarf)
    dwarves.append(yet_another_dwarf)
    group.add(yet_another_dwarf)
    dwarves.append(fourth_dwarf)
    group.add(fourth_dwarf)

    a_hammer=Hammer()
    a_pick=PickAxe()
    a_sickle=Sickle()
    a_ladder=Ladder()
    group.add(a_hammer)
    group.add(a_pick)
    group.add(a_sickle)
    group.add(a_ladder)

    the_dwarf=dwarves[dw_index]
    a_dwarf.inventory=a_pick
    another_dwarf.inventory=a_ladder
    yet_another_dwarf.inventory=a_sickle
    fourth_dwarf.inventory=a_hammer

    while True:
        if android:
            OuyaController.startOfFrame()
        delta=clock.tick(30)
        if android:
            if android.check_pause():
                android.wait_for_resume()

        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()

        for e in events:
            if e.type==pygame.QUIT:
                return
            if e.type==pygame.KEYDOWN and e.key==pygame.K_q:
                return
            if e.type==pygame.KEYDOWN and e.key==pygame.K_k:
                if not recording:
                    dw_index=(dw_index+1)%len(dwarves)
            if e.type==pygame.KEYDOWN and e.key==pygame.K_j:
                if not recording:
                    dw_index=(dw_index-1)%len(dwarves)
            if e.type==pygame.KEYDOWN and e.key==pygame.K_r:
                if not recording:
                    macro=["LOOP"]
                else:
                    program=the_dwarf.commands_behave(macro)
                    the_dwarf.behaviour=program
                    macro=[]
                recording=not recording

        the_dwarf=dwarves[dw_index]
        the_dwarf.command=None
        the_dwarf.parameter=None

        if keys[pygame.K_c] and keys[pygame.K_RIGHT]:
            if the_dwarf.inventory is not None:
                the_dwarf.command="USE-RIGHT"
        elif keys[pygame.K_c] and keys[pygame.K_LEFT]:
            if the_dwarf.inventory is not None:
                the_dwarf.command="USE-LEFT"
        elif keys[pygame.K_c] and keys[pygame.K_DOWN]:
            if the_dwarf.inventory is not None:
                the_dwarf.command="USE-DOWN"
        elif keys[pygame.K_c] and keys[pygame.K_UP]:
            if the_dwarf.inventory is not None:
                the_dwarf.command="USE-UP"
        elif keys[pygame.K_c]:
            if the_dwarf.inventory is not None:
                the_dwarf.command="USE"
        elif keys[pygame.K_UP]:
            the_dwarf.command="UP"
        elif keys[pygame.K_LEFT]:
            the_dwarf.command="LEFT"
        elif keys[pygame.K_RIGHT]:
            the_dwarf.command="RIGHT"
        elif keys[pygame.K_DOWN]:
            the_dwarf.command="DOWN"
        elif keys[pygame.K_s]:
            if the_dwarf.inventory is not None:
                the_dwarf.command="PUT"
        elif keys[pygame.K_x]:
            if the_dwarf.inventory is None:
                the_dwarf.command="TAKE"

        if recording and the_dwarf.command:
            macro.append(the_dwarf.command)

        if terrain_d.get():
            map_layer.redraw()

        group.update(delta)
        group.center(the_dwarf.rect.center)
        group.draw(screen)

        if len(sys.argv)==2 and sys.argv[1]=="--big":
            screen.blit(the_font.render("arrows-move, j/k-switch gnome",1,[255,255,255]),[5,23])
            screen.blit(the_font.render("x/s-take/drop, c-use tool",1,[255,255,255]),[5,38])
            off=53
        else:
            screen.blit(the_font.render("arrows-move, j/k-switch gnome, x/s-take/drop, c-use tool",1,[255,255,255]),[5,23])
            off=38

        for i,dwarf in enumerate(dwarves):
            if dwarf.inventory is not None:
                screen.blit(the_font.render(dwarf.inventory.name
                                            +" "+str(dwarf.inventory.durability)
                                            +" "+str(dwarf.food/50)
                                            ,1,(255,255,255)),(5,off+i*15))
            else:
                screen.blit(the_font.render("NOTHING"
                                            +" "+str(dwarf.food/50)
                                            ,1,(255,255,255)),(5,off+i*15))
        if recording:
            screen.blit(rec,(0,0))

        if len(sys.argv)==2 and sys.argv[1]=="--big":
            pygame.transform.scale(screen,(800,600),screen_real)

        pygame.display.flip()

game_loop()
