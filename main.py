import pygame
import neat
import time
import os
import random
pygame.font.init()
pygame.mixer.init()

#how big the GUI window will be, pygame display
WIDTH = 1100
HEIGHT = 680
pygame.display.set_caption("Blob Run") #name of GUI window
WIN = pygame.display.set_mode((WIDTH, HEIGHT)) #create window

#sound effects
boing_sounds = pygame.mixer.Sound("bounce.wav")
death_sound = pygame.mixer.Sound("deathsound.wav")
#background music
music = pygame.mixer.music.load("background music.wav")
pygame.mixer.music.play(-1)


#loading image assets, making a list
BLOB_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "blob0.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "blob1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "blob2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "blob3.png")))]
ENEMY_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "spikes.png")))
#enemy2_img = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "spikes1.png")))
#background and base
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "background.png")))

STAT_FONT = pygame.font.SysFont("comicscans", 50)


class Blob:
	IMGS = BLOB_IMGS
	MAX_ROTATION = 25 #how much tilt
	ROTATION_VEL = 20 #how much rotation per frame
	ANIMATION_TIME = 5 #how long to show each blob animation

	def __init__(self, x, y):
		#starting position of blob
		self.x = x
		self.y = y

		self.tilt = 0 #how much image should be tilted
		self.tick_count = 0 #used for moving/jumping later
		self.vel = 0
		self.height = self.y

		self.img_count = 0 #what image we are currently showing of the blob
		self.img = self.IMGS[0] #first blob image

	def jump(self):
		self.vel = -10.5 #go up negative vel, go down pos vel
		self.tick_count = 0 #keep track of when we last jumped
		self.height = self.y #keep track of where the blob originally jumped from

	#def move(self):
		#self.tick_count += 1 #how many times we've moved since the last frame
		#used something similar to displacement formula, num of pixels up/down the frame based on velocity
		#d = self.vel*self.tick_count + 1.5*self.tick_count**2 #self.tick_count is how many second we have been moving for

		#creating terminal velocity
		#if d >= 15:
			#d = 15

		#if d < 0:
			#d -= 2

		#change y position based on displacement
		#self.y = self.y + d

		#tilt the blob based on up or down position
		#if d < 0 or self.y < self.height + 50: #change in height upwards keep track of where we jump from
			#if self.tilt < self.MAX_ROTATION: #make sure tilt is less than max rotation
				#self.tilt = self.MAX_ROTATION
		#else: #tilting downwards
			#if self.tilt > -90: #tilt to 90 degrees
				#self.tilt -= self.ROTATION_VEL

	def draw(self, win):
		self.img_count += 1 #how many ticks have we shown an image for
		#checking what image to show based on current image count, animates it
		if self.img_count < self.ANIMATION_TIME: #5
			self.img = self.IMGS[0]
		elif self.img_count < self.ANIMATION_TIME*2: #10
			self.img = self.IMGS[1]
		elif self.img_count < self.ANIMATION_TIME*3: #15
			self.img = self.IMGS[2]
		elif self.img_count < self.ANIMATION_TIME*4: #20
			self.img = self.IMGS[3]
		elif self.img_count < self.ANIMATION_TIME*5:
			self.img = self.IMGS[2]
		elif self.img_count < self.ANIMATION_TIME*6:
			self.img = self.IMGS[1]
		elif self.img_count == self.ANIMATION_TIME*6 + 1:
			self.img = self.IMGS[0]
			self.img_count = 0

		#don't want blob to be animated as it falls down
		if self.tilt <= -80:
			self.img = self.IMGS[1] 
			self.img_count = self.ANIMATION_TIME*2 #jump back up starts at 10 so it doesn't jump a animation frame

		#rotate image about its center 
		rotated_image = pygame.transform.rotate(self.img, self.tilt)
		new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
		win.blit(rotated_image, new_rect.topleft)

	#collisions
	def get_mask(self):
		return pygame.mask.from_surface(self.img)
 

class Enemy: 
	GAP = 200 #how much space in between each enemy
	VEL = 5 #how fast each enemy is moving, blob is stationary, but all the other objects on the screen move towards the blob

	def __init__(self, x): #no y input because the height of enemy will be random
		self.x = x 
		self.height = 0

		self.top = 0 #top of enemy
		self.bottom = 0 #bottom of enemy
		self.ENEMY_TOP = pygame.transform.flip(ENEMY_IMG, False, True) #enemy on top of screen
		self.ENEMY_BOTTOM = ENEMY_IMG #enemy on bottom of screen

		self.passed = False #collision/blob successfully passed enemy
		self.set_height() #define top, bottom of enemy and position of enemy

	def set_height(self): #randomly generate where the enemy will be
		self.height = random.randrange(40, 450) #random number for top of enemy should be
		self.top = self.height - self.ENEMY_TOP.get_height() #top left position of the image of the enemy
		self.bottom = self.height + self.GAP #bottom position of the image	

	def move(self):
		self.x -= self.VEL #change x position based on velocity of each frame

	#draw both top and bottom enemy on the GUI
	def draw(self, win):
		win.blit(self.ENEMY_TOP, (self.x, self.top)) #enemy image at coords x and top
		win.blit(self.ENEMY_BOTTOM, (self.x, self.bottom))

	#collision
	#masking the image by using an 2D array (pixels going down/across) of all the pixels to tell us where the object is within the "box"
	#check if any of the pixels in the lists of the objects are matching
	def collide(self, blob, win):
		blob_mask = blob.get_mask() #get the mask for the blob
		top_mask = pygame.mask.from_surface(self.ENEMY_TOP)
		bottom_mask = pygame.mask.from_surface(self.ENEMY_BOTTOM)

		#caculating how far away the masks are from each other--offset
		top_offset = (self.x - blob.x, self.top - round(blob.y))#offset from the blob to the top enemy
		bottom_offset = (self.x - blob.x, self.bottom - round(blob.y))

		#do masks collide? finding point of collision
		b_point = blob_mask.overlap(bottom_mask, bottom_offset) #point of overlap between blob mask and the bottom enemy, if not collision, return none
		t_point = blob_mask.overlap(top_mask, top_offset)

		#check if there is collision
		if t_point or b_point:
			return True 
		return False


class Base:
	VEL = 5
	WIDTH = BASE_IMG.get_width()
	IMG = BASE_IMG

	def __init__(self, y): #x moving to the left
		self.y = y 
		self.x1 = 0 
		self.x2 = self.WIDTH

	#drawing two base images and moving them at the same speed foward
	#once one image moves off screen, it cycles to the back and continues to move foward
	#looks like we are moving one continous base image
	def move(self):
		self.x1 -= self.VEL 
		self.x2 -= self.VEL 

		#cycling the base image
		if self.x1 + self.WIDTH < 0:
			self.x1 = self.x2 + self.WIDTH
		if self.x2 + self.WIDTH < 0:
			self.x2 = self.x1 + self.WIDTH

	def draw(self, win):
		win.blit(self.IMG, (self.x1, self.y))
		win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, blob, enemy, base, score):
	win.blit(BG_IMG, (0,0)) #draw on the window starting at the top left
	blob.draw(win) 
	for enemy in enemy:
		enemy.draw(win)

	#score
	text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
	win.blit(text,(WIDTH - 10 - text.get_width(), 10))

	base.draw(win)

	#updates display
	pygame.display.update()
 

def main():
	blob = Blob(230, 200)
	base = Base(552)
	enemy = [Enemy(500)]
	win = pygame.display.set_mode((WIDTH, HEIGHT))
	clock = pygame.time.Clock()
	score = 0
	lost = False 
	lost_count = 0
	FPS = 20
	game_active = True 
	blob_vel= 5
	lost_font = pygame.font.SysFont("comicsans", 70)


	def redraw_window():
		if lost:
			lost_label = lost_font.render("You Lost!! Play again?", 1, (255,255,255))
			WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))
		pygame.display.update() #refreshes the display, redraws on the surfaces while we loop, redraw will update the image


	run = True
	while run:
		redraw_window()
		clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
		

		#moving of the blob
		keys = pygame.key.get_pressed()
		if keys[pygame.K_s] and blob.y + blob_vel + 15 < HEIGHT: # down
			blob.y += blob_vel
			boing_sounds.play()
        #up and limits so it can't move off the screen
		if keys[pygame.K_w] and blob.y - blob_vel > 0: 
			blob.y -= blob_vel
			boing_sounds.play()

		#moving blob
		#blob.move()

		
		add_enemies = False 
		rem = []


		if score == -1:
			lost = True
			lost_count += 1
		if lost:
			if lost_count > FPS*2:
				run = False
			else:
				continue

		for enemies in enemy:
			if enemies.collide(blob, win):
				#blob.move()
				score = -1
				death_sound.play()
				enemy.remove(enemies)
				lost = True 

			if enemies.x + enemies.ENEMY_TOP.get_width() < 0: #if enemy is completely off the screen, then we remove the enemy
				rem.append(enemies)

			if not enemies.passed and enemies.x < blob.x: #check if blob has passed the enemy
				enemies.passed = True 
				add_enemies = True 

			enemies.move()

		#generate new enemy after blob passed the first one
		if add_enemies:
			score += 1
			enemy.append(Enemy(500))

		for r in rem:
			enemy.remove(r)

		if blob.y + blob.img.get_height()>=730:
			pass

		#moving the base
		base.move()

		draw_window(win, blob, enemy, base, score)



def main_menu():
    title_font = pygame.font.SysFont("comicscans", 70)
    run = True
    while run:
        WIN.blit(BG_IMG, (0,0))
        title_label = title_font.render("Press screen to begin the game...", 1, (255,255,255))
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 350))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()
    pygame.quit()
    quit()

main_menu()

