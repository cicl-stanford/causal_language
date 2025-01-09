import sys
import pygame
from pygame.locals import *
import pymunk
import pymunk.pygame_util
import itertools
import json
import numpy as np
import math
from pymunk import Vec2d
import collections #for keeping the order in which dictionaries were created
import time
import pandas as pd
import os
from collections import defaultdict

# WARNING: Pygame and Pymunk have reverse labeling conventions along the Y axis.
# For pymunk the top is higher values and for pygame the top is lower values
# be aware when interpreting coordinates

class World():

	def __init__(self, gate=False, start_step=0):
		self.width = 800
		self.height = 600
		self.ball_size = 60
		self.box_size = (70,70)
		self.speed = 200 # scales how fast balls are moving 
		self.step_size = 1/50.0
		self.step_max = 500 # step at which to stop the animation
		self.step = start_step # used to record when events happen 
		self.space = pymunk.Space()
		self.events = {'collisions': [],
						'wall_bounces': [],
						'button_presses': [],
						'outcome': None,
						'final_target_position': None,
						'final_target_time': None}
						# 'outcome_fine': {"position": None, "time": None}} # used to record events 
		# containers for bodies and shapes
		self.bodies = collections.OrderedDict()
		self.shapes = collections.OrderedDict()	
		self.sprites = collections.OrderedDict()

		self.record_bodies = {'A', 'B', 'D', 'E', 'box', 'gate'}
		self.record_outcome = True
		self.end_delay = 30
		self.cause_ball = 'A'
		self.target_ball = 'B'
		self.gate = gate

		self.collision_types = {
			'static': 0,
			'dynamic': 1,
			'gate': 2,
			'gate_sensor': 3,
			'button': 4,
			'button_sensor': 5,
			'button_stopper': 6
		}

		# add walls 
		self.add_wall(position = (400, 590), length = 800, height = 20, name = 'top_wall')
		self.add_wall(position = (400, 10), length = 800, height = 20, name = 'bottom_wall')

		# Add walls for presence or absence of a gate
		if not self.gate:
			self.add_wall(position = (10, 500), length = 20, height = 200, name = 'top_left_wall')
			self.add_wall(position = (10, 100), length = 20, height= 200, name = 'bottom_left_wall')
		else:
			# Top left wall setup
			self.add_wall(position = (10, 540.8425), length = 20, height = 78.334, name = 'top_top_left_wall')
			self.add_wall(position = (10, 432.5075), length = 20, height = 78.335, name = 'bottom_top_left_wall')


			# Bottom left wall setup
			self.add_wall(position=(10, 167.5025), length=20, height=78.335, name='top_bottom_left_wall')
			self.add_wall(position=(10, 59.1675), length=20, height=78.335, name='bottom_bottom_left_wall')


	###################### Simulation setup and running #######################
	def add_wall(self, position, length, height, name):
		body = pymunk.Body(body_type = pymunk.Body.STATIC)
		body.position = position
		body.name = name
		wall = pymunk.Poly.create_box(body, size = (length, height))
		wall.elasticity = 1
		# wall.name = name 
		wall.collision_type = self.collision_types['static']
		self.space.add(wall)
		return wall


	# Separate code to setup and run animation if desired
	def animation_setup(self):
		# animation setup
		pygame.init()
		self.clock = pygame.time.Clock()
		self.screen = pygame.display.set_mode((self.width, self.height))
		pygame.display.set_caption("Animation")
		self.pic_count = 0 # used for saving images 

		for bname in self.bodies:
			if 'sensor' not in bname:
				sprite = pygame.image.load(os.path.join(self.img_dir, 'figures/' + bname + '.png'))
				self.sprites[bname] = sprite

	def animation_step(self, save, save_dir="", save_frames=[]):
		# quit conditions
		for event in pygame.event.get():
			if event.type==QUIT:
				pygame.quit()
				sys.exit(0)
			elif event.type == KEYDOWN and event.key == K_ESCAPE:
					animate=False

		if len(save_frames)==0 or self.pic_count in save_frames:

			# draw screen, bacground and bodies
			self.screen.fill((255,255,255)) #background
			if not self.gate:
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['red'], [0,200,20,200])
			else:
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['red'], [0,206.67,20,187]) #goal

			for body in self.bodies:
				if 'sensor' not in body:
					self.update_sprite(body = self.bodies.get(body), sprite = self.sprites.get(body),screen = self.screen)

			# pygame.draw.rect(screen, pygame.color.THECOLORS['red'], [0,200,20,200]) #goal
			pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,0,800,20]) #top wall
			pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,580,800,20]) #bottom wall

			if not self.gate:
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,0,20,200])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,400,20,200])
			else:
				# Top left drawing with button
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,20,20,78.334]) #top left
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,128.334,20,78.335])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,98.334,10,30])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['grey'], [5,98.334,5,30])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['grey'], [5,95.334,15,3])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['grey'], [5,128.334,15,3])

				# Bottom left drawing with button
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,393.339,20,78.335])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,501.674,20,79])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['black'], [0,471.674,10,30])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['grey'], [5,471.674,5,30])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['grey'], [5,468.674,15,3])
				pygame.draw.rect(self.screen, pygame.color.THECOLORS['grey'], [5,501.674,15,3])

			# Update the screen
			pygame.display.flip()
			pygame.display.update()
			self.clock.tick(100)

			if save:
				if save_dir == "":
					save_dir = 'figures/frames'
				pygame.image.save(self.screen, os.path.join(save_dir, 'animation'+'{:03}'.format(self.pic_count)+'.png'))
		self.pic_count += 1

	# Procedure to run simulation. Returns events dict or events dict and path info dependent on the value of rec_paths
	def simulate(self, animate=False, noise=0, perturb=0, prob=0, save=False, rec_paths=False, info=[], img_dir="", save_dir="", save_frames=[], cut_sim=False):
		self.img_dir = img_dir

		self.collision_setup()
		done = False # pointer to say when animation is done
		if rec_paths:
			paths = {}
			for name, body in self.bodies.items():
				if name in self.record_bodies:
					paths[name] = {'position': [], 'velocity': []}

		# animation setup
		if animate:
			self.animation_setup()

		while not done:
			# animation code
			if animate:
				self.animation_step(save, save_dir, save_frames)

			# cf manipulations 
			for action in info:
				if action['action'] == 'remove':
					self.remove(obj=action['obj'], step=action['step'], animate=animate)
				if action['action'] == 'perturb':
					self.perturb(obj=action['obj'], step=action['step'], magnitude=action['magnitude'])
				if action['action'] == 'noise':
					self.apply_noise(obj=action['obj'], step=action['step'], noise=noise)
				if action['action'] == 'earthquake':
					self.earthquake(obj=action['obj'], prob=action['prob'], noise=action['noise'], earthquake_type=action['earthquake_type'])

			# If we want to record paths, save the position and velocity for each body
			# on the recording list
			if rec_paths:
				for name, body in self.bodies.items():
					if name in self.record_bodies:
						path = paths[name]
						positions = path['position']
						velocities = path['velocity']

						x,y = body.position
						x_vel,y_vel = body.velocity

						positions.append([x,y])
						velocities.append([x_vel,y_vel])

			# check completion
			done = self.end_clip(cut_sim)

			# Update the world itself
			self.space.step(self.step_size)
			self.step += 1

		# Double check collisions are in temporal order and return
		collisions = self.events['collisions']
		assert all([collisions[i]['step'] <= collisions[i+1]['step'] for i in range(len(collisions) - 1)])
		if not rec_paths:
			return self.events
		else:
			return self.events, paths

	# Procedure to add a ball
	def add_ball(self, position, velocity, size, name):
		mass = 1
		radius = size/2
		moment = pymunk.moment_for_circle(mass, 0, radius)
		body = pymunk.Body(mass, moment)
		body.position = position
		body.size = (size,size)
		body.angle = 0
		velocity = [x*self.speed for x in velocity] 
		body.apply_impulse_at_local_point(velocity) #set velocity
		body.name = name 
		shape = pymunk.Circle(body, radius)
		shape.elasticity = 1.0
		shape.friction = 0
		shape.collision_type = self.collision_types['dynamic']
		self.space.add(body, shape)
		self.bodies[name] = body
		self.shapes[name] = shape
		return body, shape

	# Procedure to add a box. Velocity update is modified within
	def add_box(self, position, size, angle, name):
		mass = 1
		moment = pymunk.moment_for_box(mass, size)
		body = pymunk.Body(mass, moment)
		body.position = position
		body.size = size
		body.angle = angle
		velocity = (0,0)

		# Create custom velocity update and override standard
		def update_velocity(body, gravity, damping, dt):
			pymunk.cp.cpBodyUpdateVelocity(body._body, tuple(gravity), .96, dt)
		body._set_velocity_func(update_velocity)


		body.name = name
		shape = pymunk.Poly.create_box(body, size)
		shape.elasticity = 1.0
		# I don't think this friction parameter has desired effect
		# worth further investigation
		# shape.friction = 1.0
		shape.collision_type = self.collision_types['dynamic']
		self.space.add(body, shape)
		self.bodies[name] = body
		self.shapes[name] = shape
		return body, shape

	# Procedure to add a button based on starting button position (top or bottom)
	# anda a starting gate position
	# Also adds the corresponding sensor to stop the button
	def add_button(self, pos, gate_pos):
		body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
		if pos == 'top':
			if gate_pos == 'top':
				body.position = (10, 486.675)
			else:		
				body.position = (20, 486.675)
		if pos == 'bottom':
			if gate_pos == 'bottom':
				body.position = (10, 113.326)
			else:
				body.position = (20, 113.326)
		body.name = pos
		# Avoid overlap
		body.size = (20,29.9)
		body.angle = 0
		shape = pymunk.Poly.create_box(body, body.size)
		shape.elasticity = 1.0
		shape.collision_type = self.collision_types['button']
		self.space.add(body, shape)
		self.bodies[body.name] = body
		self.shapes[body.name] = shape
		if pos == 'top':
			# self.add_sensor((-10,486.675), 'top_back_sensor', 'button')
			self.add_wall(position=(-10, 486.675), length=20, height=30, name='top_button_stopper')
			self.add_sensor((40, 486.675), 'top_front_sensor', 'button')
		elif pos == 'bottom':
			# self.add_sensor((-10,113.335), 'bottom_back_sensor', 'button')
			self.add_wall(position=(-10, 113.335), length=20, height=30, name='bottom_button_stopper')
			self.add_sensor((40,113.335), 'bottom_front_sensor', 'button')
		return body, shape

	# Add a sensor
	def add_sensor(self, pos, name, stop_obj):
		body = pymunk.Body(body_type=pymunk.Body.STATIC)
		body.position = pos
		body.name = name
		body.size = (20, 20)
		body.angle = 0
		shape = pymunk.Poly.create_box(body=body, size=body.size)
		if stop_obj == 'button':
			shape.collision_type = self.collision_types['button_sensor']
		elif stop_obj == 'gate':
			shape.collision_type = self.collision_types['gate_sensor']
		shape.sensor = True
		self.space.add(body, shape)
		self.bodies[body.name] = body
		self.shapes[body.name] = shape
		return body, shape

	# Add the gate given a starting position. If the gate is added
	# buttons and and stopping sensors will be added as well.
	def add_gate(self, start_pos):
		body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
		if start_pos == 'middle':
			body.position = (30, 300)
		elif start_pos == 'top':
			body.position = (30, 486.67)
		elif start_pos == 'bottom':
			body.position = (30, 113.33)
		# Avoid tapping the wall and stopping the gate early
		size = (19.9, 186.67)
		body.size = size
		body.angle = 0
		body.name = 'gate'
		shape = pymunk.Poly.create_box(body, size)
		shape.elasticity = 1.0
		shape.collision_type = self.collision_types['gate']
		self.space.add(body, shape)
		self.bodies['gate'] = body
		self.shapes['gate'] = shape

		self.gate = body

		self.add_button('top', start_pos)
		self.add_button('bottom', start_pos)
		self.add_sensor((30, 402), 'gate_top_sensor', 'gate')
		self.add_sensor((30, 197), 'gate_bottom_sensor', 'gate')
		return body, shape


	def flipy(self, y):
		"""Small hack to convert chipmunk physics to pygame coordinates"""
		return -y+600

	# Code to update the object image on the screen
	def update_sprite(self,body,sprite,screen):
		p = body.position
		p = Vec2d(p.x, self.flipy(p.y))
		angle_degrees = math.degrees(body.angle)
		rotated_shape = pygame.transform.rotate(sprite, angle_degrees)
		offset = Vec2d(rotated_shape.get_size()) / 2.
		p = p - offset
		screen.blit(rotated_shape, p)

	# setup collision handlers 
	def collision_setup(self):	
		handler_dynamic = self.space.add_collision_handler(self.collision_types['dynamic'], self.collision_types['dynamic'])
		handler_dynamic.begin = self.collisions

		handler_ball_wall = self.space.add_collision_handler(self.collision_types['dynamic'], self.collision_types['static'])
		handler_ball_wall.begin = self.ball_other_col

		handler_ball_gate = self.space.add_collision_handler(self.collision_types['dynamic'], self.collision_types['gate'])
		handler_ball_gate.begin = self.ball_other_col

		handler_ball_button = self.space.add_collision_handler(self.collision_types['dynamic'], self.collision_types['button'])
		handler_ball_button.begin = self.ball_button_col

		handler_button_sensor = self.space.add_collision_handler(self.collision_types['button'], self.collision_types['button_sensor'])
		handler_button_sensor.begin = self.button_sensor_col
		# handler_button_sensor.post_solve = self.button_sensor_col

		handler_button_wall = self.space.add_collision_handler(self.collision_types['button'], self.collision_types['static'])
		handler_button_wall.pre_solve = self.button_wallstop_col

		handler_gate_wall = self.space.add_collision_handler(self.collision_types['gate'], self.collision_types['static'])
		handler_gate_wall.begin = self.gate_wall_col

		handler_gate_sensor = self.space.add_collision_handler(self.collision_types['gate'], self.collision_types['gate_sensor'])
		handler_gate_sensor.begin = self.gate_sensor_col

	# handle dynamic events
	def collisions(self,arbiter,space,data):
		# print arbiter.is_first_contact #checks whether it was the first contact between the shapes 
		event = {
			'objects': {arbiter.shapes[0].body.name,arbiter.shapes[1].body.name},
			'step': self.step
		}
		self.events['collisions'].append(event)
		return True

	# handle dynamic events
	def ball_other_col(self,arbiter,space,data):
		# print arbiter.is_first_contact #checks whether it was the first contact between the shapes 
		event = {
			'objects': {arbiter.shapes[0].body.name,arbiter.shapes[1].body.name},
			'step': self.step
		}
		self.events['wall_bounces'].append(event)
		return True

	# Handle collisions between buttons and balls. Record events and 
	# Set the button and gate in motion.
	def ball_button_col(self, arbiter, space, data):
		event = {
			'objects': {arbiter.shapes[0].body.name, arbiter.shapes[1].body.name},
			'step': self.step
		}
		self.events['button_presses'].append(event)

		button = arbiter.shapes[1].body
		button.velocity = (-20,0)
		if button.name == 'top':
			self.gate.velocity = (0,60)
		elif button.name == 'bottom':
			self.gate.velocity = (0,-60)
		else:
			raise Exception('Invalid button name: {}'.format(button.name))

		return True

	# Stop the button when it collides with the sensor
	def button_sensor_col(self, arbiter, space, data):
		button = arbiter.shapes[0].body
		button.velocity = (0,0)
		return True

	# Stop the button when it hits the back wall
	def button_wallstop_col(self, arbiter, space, data):
		button = arbiter.shapes[0].body
		x,y = button.velocity
		if x < 0:
			button.velocity = (0,0)
		return True

	# Stop the gate when it collides with the wall
	def gate_wall_col(self, arbiter, space, data):
		gate = arbiter.shapes[0].body
		gate.velocity = (0,0)
		return True

	# Stop the gate when it collides with a stop sensor
	def gate_sensor_col(self, arbiter, space, data):
		gate = arbiter.shapes[0].body
		gate.velocity = (0,0)
		# This code resets the buttons to the a pressable position after
		# the gate arrives back in the middle. It's constrained not to run
		# on the first step so that the buttons are not activated as soon
		# as the clip starts (when the gate is initialized)
		if self.step != 0:
			sensor = arbiter.shapes[1].body.name
			self.bodies['bottom'].velocity = (20,0)
			self.bodies['top'].velocity = (20,0)
		return True

	# A method to check whether to end the simulation and record outcome info
	# Still need to see how this plays with sufficiency test and cut_sim
	def end_clip(self, cut_sim=False):

		target = self.bodies[self.target_ball]
		exit = target.position[0] < -self.ball_size/2

		# Kills simulation if the target exits or if we reach the max step

		if exit:

			if self.record_outcome:
				# Only set the outcome events if they are currently unassigned
				if self.events['outcome'] == None:
					self.events['outcome'] = 1
					self.events['final_target_position'] = target.position
					self.events['final_target_time'] = self.step

				# Once you meet the delay, cut the simulation
			if (self.step - self.events['final_target_time']) == self.end_delay:
				pygame.display.quit()
				return True


		if self.step > self.step_max:

			# Might have already recorded an outcome if the ball exited, but we are still in
			# the "end_delay" period, so still need to check and make sure not to overwrite
			# Also need to check for noting the final outcome event
			if self.record_outcome:
				# Only set the outcome events if they are currently unassigned
				if self.events['outcome'] == None:
					self.events['outcome'] = int(exit)
					self.events['final_target_position'] = target.position
					self.events['final_target_time'] = self.step

			pygame.display.quit()
			return True


		return False

	###################################################################

	############ Counterfactual manipulation procedures ###############
	def remove(self,obj,step,animate):
		if self.step == step:
			self.space.remove(self.shapes[obj]) #remove body from space 
			self.space.remove(self.bodies[obj]) #remove body from space 
			del self.bodies[obj] #remove body 
			del self.shapes[obj] #remove shape
			if animate: 		
				del self.sprites[obj] #remove sprite 

	def perturb(self,obj,step,magnitude=0):
		if self.step == step:
			b = self.bodies[obj]
			b.position = (b.position.x+self.gaussian_noise()*magnitude,
				b.position.y+self.gaussian_noise()*magnitude)

	# step-wise noise
	# use when there's a removed collision (represent uncertainty about where the ball would have gone)
	# apply gaussian noise to velocity at each step
	# step := which step do we start applying noise (the removed collision point)
	# noise := standard deviation of the angle perturbation
	def apply_noise(self,obj,step,noise):
		if not noise == 0:
			b = self.bodies[obj]
			if self.step > step:
				x_vel = b.velocity[0]
				y_vel = b.velocity[1]
				perturb = self.gaussian_noise()*noise
				cos_noise = np.cos(self.deg_to_rad(perturb))
				sin_noise = np.sin(self.deg_to_rad(perturb))
				x_vel_noise = x_vel * cos_noise - y_vel * sin_noise
				y_vel_noise = x_vel * sin_noise + y_vel * cos_noise
				b.velocity = x_vel_noise,y_vel_noise

	# Box-Muller transform
	def gaussian_noise(self):
		u = 1 - np.random.random()
		v = 1 - np.random.random()
		return np.sqrt(-2*np.log(u)) * np.cos(2 * np.pi * v)

	def deg_to_rad(self, degrees): return degrees*(math.pi/180)

	##################################################################

################ Model 1 for pragmatic judgement #################


# Given a trial dictionary, setup the world and simulate the trial
def run_trial(trial, animate=False, noise=0, perturb=0, prob=0, rec_paths=False, save=False, info=[], img_dir="", save_dir="", save_frames=[], cut_sim=False):
	balls = trial['balls']
	if 'boxes' in trial:
		boxes = trial['boxes']
	else:
		boxes = []

	w = World(gate=('gate' in trial))
	for ball in balls:
		w.add_ball(tuple(ball['position']), tuple(ball['velocity']), w.ball_size, ball['name'])
	for box in boxes:
		angle = box['angle'] if 'angle' in box else 0
		w.add_box(tuple(box['position']), w.box_size, w.deg_to_rad(angle), box['name'])
	if w.gate:
		gate = trial['gate']
		w.add_gate(gate['start_pos'])

	return w.simulate(animate=animate, noise=noise, perturb=perturb, prob=prob, save=save, rec_paths=rec_paths, info=info, img_dir=img_dir, save_dir=save_dir, save_frames=save_frames, cut_sim=cut_sim)


# A procedure to determine which balls are downstream of a given ball in a 
# chain of collisions, and the timestep at which those items enter the chain
# Returns a list of tuples indicating the items in the chain and the time steps
# at which they enter the chain
def collision_chain(collisions, in_chain, start_time, reverse_time=False):
	# Base case. When the list is empty return the empty list
	if collisions == []:
		return []
	else:
		# Otherwise grab the first collision. Diff is all balls in the collision
		# that are not currently in the causal chain
		hd = collisions[0]
		diff = hd['objects'] - in_chain

		# If both balls are not in the causal chain, then the collision is not connected
		# to the causal chain. Because the collisions are sorted by time, we know it can be ignored

		# If both balls are already in the causal chain, then they already should have noise applied
		# (or have been removed). We don't need to add noise.

		# If only one ball is not in the causal chain, then this collision makes that ball a part
		# of the causal chain. Check to make sure it did not occur simultaneously with the previous
		# collision (a counterexample). If it did not then we add that ball and the timestep of the
		# collision to the output. We also add the ball to the set of in_chain balls and update the
		# timestep

		if not reverse_time:
			time_condtion = hd['step'] > start_time
		else:
			# For the reverse situation we want to note simultaneous collisions so <=
			time_condtion = hd['step'] <= start_time

		if len(diff) == 1 and time_condtion:
			b2 = diff.pop()
			new_set = in_chain | {b2}
			return [(b2, hd['step'])] + collision_chain(collisions[1:], new_set, hd['step'], reverse_time=reverse_time)
		else:
			return collision_chain(collisions[1:], in_chain, start_time, reverse_time=reverse_time)
		
# Convenience procedure to return the actual outcome of a trial
def outcome(trial):
	events = run_trial(trial=trial)
	outcome = events["outcome"]
	return outcome

# Run the whether cf test on a trial given a trial, candidate cause, target entity,
# asuncertainty noise value, and number of samples
# Return a value indicating the proportion of samples in which the candidate satisfied the whether
# cause definition.
# In this case, the test is implemented that causers are distinguished from preventers.
# Causers will receive positive whether cause outcomes and preventers negative
def whether_test(trial, candidate, target, noise, num_samples, background_removals=[], animate=False, test_noise=False):
	# Run the simulation naturally
	info = []
	for entity in background_removals:
		info.append({
			'action': 'remove',
			'obj': entity,
			'step': 0
			})

	events = run_trial(trial=trial, animate=animate, info=info)

	# Determine the chain of collisions and the outcome
	col_actual = events['collisions']
	in_chain = {candidate}
	noise_steps = collision_chain(col_actual, in_chain, -1)
	outcome_actual = events['outcome']
	# print(outcome_actual)

	# Add cf removal and noise manipulations
	# info = []
	info.append({
		'action': 'remove',
		'obj': candidate,
		'step': 0
		})

	for item in noise_steps:
		info.append({
			'action': 'noise',
			'obj': item[0],
			'step': item[1] 
		})

	# Run the counterfactual world and get the outcome for n samples
	outcome_cf = np.zeros(num_samples)
	for i in range(num_samples):	
		events_cf = run_trial(trial=trial, animate=animate, noise=noise, info=info)
		outcome_cf[i] = events_cf['outcome']
	# print(outcome_cf)


	# If the actual outcome is different from the counterfactual one, return true
	if not test_noise:
		return np.mean(outcome_actual - outcome_cf)
	else:
		return np.mean(outcome_actual - outcome_cf), {'info': info}


# Run the how cause on a given trial for a candidate and target. Perturb scales
# the purturbation amount.
# Currently I've been running the how test for a single sample on the assumption
# that it is essentially deterministic despite the random perturbation. This is not
# entirely true, and some simulations have revealed that depending on the trial and
# size of the perturbation, random effects can make a difference. Given this we
# might want to think more about our use of this test and whether we want to run more
# samples and re-think how we combine them.
def how_test(trial, candidate, target, perturb, num_samples, animate=False):
	events = run_trial(trial=trial, animate=animate)
	a,b = events['final_target_position']
	outcome_actual = [a,b]

	# apply perturbation
	info = []
	info.append({
		'action': 'perturb',
		'obj': candidate,
		'step': 0,
		'magnitude': perturb
		})

	# run forward cf world and record outcome
	outcome_cf = np.zeros((num_samples,2))
	for i in range(num_samples):
		cf_events = run_trial(trial=trial, animate=animate, perturb=perturb, info=info)
		x,y = cf_events['final_target_position']
		outcome_cf[i,:] = [x,y]

	# return true if the fine outcomes are different
	return np.all(outcome_actual != outcome_cf, axis=1)


# Computes the sufficiency test on a given trial, candidate, and target
# for a noise value and number of samples and given set of alternatives
# Returns a value indicating the proportion of samples for which the candidate is
# determined sufficient to make the target go through the gate
def sufficient_test(trial, candidate, target, alternatives, noise, num_samples, animate=False, test_noise=False, event_test=True):
	events = run_trial(trial=trial, animate=False)
	# Get the outcome
	outcome_actual = events['outcome']

	# some objects may need noise after you remove alternatives
	# Obtain all relevant collisions and sort by timestep
	col_actual = events['collisions']
	noise_steps = []
	for alt in alternatives:
		noise_steps = noise_steps + collision_chain(col_actual, {alt}, -1)
	noise_steps.sort(key=lambda x: x[1])

	# We can then filter noise additions to ensure that they only take place
	# for non alternatives and only the first time for each
	first_cause = False
	first_target = False
	filtered_noise = []
	for item in noise_steps:
		if item[0] == candidate and not first_cause:
			first_cause = True
			filtered_noise.append(item)
		if item[0] == target and not first_target:
			first_target = True
			filtered_noise.append(item)


	# Setup manipulations for counterfactual
	info_cf = []
	for obj in alternatives:
		manip = {
			'action': 'remove',
			'obj': obj,
			'step': 0
		}
		info_cf.append(manip)

	for item in filtered_noise:
		manip = {
			'action': 'noise',
			'obj': item[0],
			'step': item[1]
		}
		info_cf.append(manip)


	# setup manipulations for counterfactual contingency
	info_cf_cont = []
	# Collect all noise additions from the candidate and alternatives
	noise_add_cont = collision_chain(events['collisions'], {candidate}, -1) + filtered_noise
	# filter out any noise application that isn't the target (since the target
	# is the only body left) and add the first if one exists
	noise_add_cont = [x for x in noise_add_cont if x[0] == target]
	# Multiple things could have hit the target in separate chains
	# Sort by timestep and choose the first one if it exists
	# Add it to manipulations for the counterfactual contingency
	noise_add_cont.sort(key=lambda x: x[1])
	if len(noise_add_cont) > 0:
		tar_noise = noise_add_cont[0]
		info_cf_cont.append({'action': 'noise', 'obj': tar_noise[0], 'step': tar_noise[1]})


	# add removals for counterfactual contingency (remove everything except target)
	for obj in alternatives:
		manip = {
			'action': 'remove',
			'obj': obj,
			'step': 0
		}
		info_cf_cont.append(manip)

	manip = {
		'action': 'remove',
		'obj': candidate,
		'step': 0
	}
	info_cf_cont.append(manip)

	# Run the counterfactuals and cf contingencies
	# outcome_cf = np.zeros(num_samples)
	# outcome_cf_cont = np.zeros(num_samples)

	outcomes = np.zeros(num_samples)
	for i in range(num_samples):
		events_cf = run_trial(trial=trial, animate=animate, noise=noise, info=info_cf, cut_sim=True)
		outcome_cf = events_cf['outcome']

		events_cf_cont = run_trial(trial=trial, animate=animate, noise=noise, info=info_cf_cont, cut_sim=True)
		outcome_cf_cont = events_cf_cont['outcome']

		outcomes[i] = (outcome_actual == outcome_cf) and (outcome_cf != outcome_cf_cont)

		# check whether the sufficiency events took place in the actual world
		if event_test:

			actual_collisions = events['collisions']
			cf_collisions = events_cf['collisions']

			actual_bpresses = events['button_presses']
			cf_bpresses = events_cf['button_presses']

			# Checks whether each counterfactual collision and each counterfactual button press
			# took place in the actual world
			collision_containment = [col in actual_collisions for col in cf_collisions]
			bpress_containment = [press in actual_bpresses for press in cf_bpresses]

			containment = (all(collision_containment) and all(bpress_containment))

			outcomes[i] = outcomes[i] and containment


	if not test_noise:
		return np.mean(outcomes)
	else:
		return np.mean(outcomes), {'info_cf': info_cf, 'info_cf_cont': info_cf_cont}


# Procedure to test whether the candidate cause is moving
# Probably need to extend this for causal chains with stationary causes
# Though not sure yet how it should inform the model
def moving_test(trial, candidate, target):
	# Get the event and paths
	events, paths = run_trial(trial=trial, rec_paths=True)
	moving = True
	# For all collisions if the candidate and the target are in a collision
	# and the candidate's velocity is zero beforehand, then the candidate
	# cause was stationary
	for col in events["collisions"]:
		objects = col["objects"]
		if candidate in objects and target in objects:
			candidate_vel = paths[candidate]['velocity']
			if candidate_vel[col['step'] - 1] == [0.0, 0.0]:
				moving = False

	return moving

# Procedure to test whether the candidate cause is unique
# Uniqueness here is defined as the candidate (A) being the only object to directly contact the target (B)
def unique_test(trial,
				candidate='A', 
				target='B',
				alternatives={'D', 'box'}):

	tr_events = run_trial(trial=trial, rec_paths=False)
	
	cols = tr_events['collisions']
	
	# initialize outcome to not unique
	outcome = 0
	
	# loop through each collision
	for col in cols:
		
		# if the target is in the collision and it collides with one of the alternatives
		# it is not unique, return 0.
		if target in col['objects']:
			set_int = alternatives.intersection(col['objects'])

			if len(set_int) > 0:
				return 0
			
			# If the candidate is the collision it is possibly unique.
			# Return 1 if loop completes with no change.
			elif candidate in col['objects']:
				outcome = 1
		
	return outcome



################## Procedures to generate aspect representations for the base of the model ####################

### First some procedures to determine relevant alternatives in each trial ###

# Extract the object from a trial dictionary
# Currently doesn't the gates
def trial_entities(tr):
	entities = set()
	if "balls" in tr:
		for ball in tr['balls']:
			entities.add(ball['name'])

	if 'boxes' in tr:
		for box in tr['boxes']:
			entities.add(box['name'])

	return entities

# Given a set of alternatives, return all subsets of the set
def subset(alternatives):
	if len(alternatives) == 0:
		return [[]]
	else:
		x = alternatives[0]
		return subset(alternatives[1:]) + [[x] + y for y in subset(alternatives[1:])]

# Given a trial, assess for each entity in the scene if it
# is a whether cause in all counterfactual contingencies. Record
# outcome for each entitiy and removal set. Don't consider the target

# Currently simulations are deterministic for simplicity.
# This could be modified and extended

# Returns a dictionary of lists where each key in the dictionary maps from
# an entity in the trial to a list where the items of the list are pairs
# denoting a removal set, and the resulting whether test outcome given that removal
# set
def assess_trial(test_trial, animate=False):

	# Extract all the entities in the trial
	entities = trial_entities(test_trial)

	# Remove the target entity, as it can't have causal status
	entities = entities - {'B'}


	e_record = {}
	for e in entities:
		alternatives = entities - {e}
		cfs = []
		if animate:
			print("Entity")
			print(e)
		# Consider each removal set
		for removal_set in subset(list(alternatives)):
			if animate:
				print("Removed")
				print(removal_set)
			wh_value = whether_test(trial = test_trial, candidate=e, target='B', noise=0, num_samples=1, background_removals=removal_set, animate=animate)


			cfs.append((removal_set, wh_value))

		if animate:
			print()

		e_record[e] = cfs

	return e_record


# Given a set of trials, compute whether tests in all counterfactual contingencies
# Then convert to a dataframe organized by trial, entitiy, and removal set with
# information about causer and preventer status

# Allows us to save the info about alternative status so it doesn't need to be
# re-generated each time
def create_trial_assessment_df(trials, save=False):
	# Initialize dict
	cont_dict = {'trial':[], 'entity':[], 'removal_set':[], 'value':[]}

	# Loop across the trials
	for tr in trials:
		trial_num = tr['trial']
		record = assess_trial(tr)

		# For each entity
		for e, contingencies in record.items():
			# Consider each contingency
			for cont,v in contingencies:
				# Append the trial, entity in consideration, the removal set,
				# and the corresponding whether value
				cont_dict['trial'].append(trial_num)
				cont_dict['entity'].append(e)
				cont_dict['removal_set'].append(cont)
				cont_dict['value'].append(v)

	# Convert to a dataframe
	df_cont = pd.DataFrame(cont_dict)
	# Note whether the entity is a causer or preventer in each contingency
	df_cont['is_causer'] = df_cont['value'] > 0
	df_cont['is_preventer'] = df_cont['value'] < 0
	# Produce new df that makes whether an entity in a trial is a preventer
	# or causer for any removal set
	alternative_status = df_cont.groupby(['trial', 'entity'], as_index=False)[['is_causer', 'is_preventer']].any()

	# Save df check
	if save:
		alternative_status.to_csv('useful_csvs/alternative_status.csv')

	return alternative_status

# Returns a list of sets, where the set is all the valid alternatives
# in the trial whose number corresponds to the index
def load_alternative_assessments(alternative_status=None):
	# If the alternatives statuses are not provided, try to load them
	if alternative_status is None:
		try: 
			alternative_status = pd.read_csv('useful_csvs/alternative_status.csv')
		except:
			raise Exception("No alternatives assessment file, please provide dataframe or re-generate.")

	# Get list of trials
	trials = alternative_status['trial'].unique()

	# For each trial
	trial_alternatives = []
	for trial_num in trials:
		df_temp = alternative_status[alternative_status['trial'] == trial_num]

		trial_set = set()
		for index, row in df_temp.iterrows():
			# Add the entity as a potential alternative if it is a causer in some contingency
			if row['is_causer']:
				trial_set.add(row['entity'])

		trial_alternatives.append(trial_set)

	return trial_alternatives



# Return the aspect representation for the trial given the candidate, target, set of
# valid alternatives, and test parameters
def aspect_rep(trial, candidate, target, alternatives, noise=2, perturb=0.01, num_samples=100):

	# Check if the candidate is in the trial
	trial_entities = {ent['name'] for ent in trial['balls']}
	if 'boxes' in trial:
		trial_entities.add('box')
	# Remove candidate if it is a potential alternative for the trial
	alternatives = alternatives - {candidate}

	if candidate in trial_entities:
		o = outcome(trial)
		w = whether_test(trial, candidate, target, noise, num_samples)
		h = float(how_test(trial, candidate, target, perturb, 1))
		s = sufficient_test(trial, candidate, target, alternatives, noise, num_samples)
		mov = moving_test(trial, candidate, target)
		un = unique_test(trial, candidate, target, alternatives)
		return [w,h,s,mov,un,o]
	else:
		return [np.nan]*5


def make_aspect_file(trials, aspect_file_name, noise_val, num_samples, compute_alternatives=True, candidates=["A"]):

	if type(trials) == str:	
		trials = load_trials(trials)

	if compute_alternatives:
		alternative_status = create_trial_assessment_df(trials)
		trial_alternatives = load_alternative_assessments(alternative_status)
	else:
		trial_alternatives = load_alternative_assessments()

	aspect_reps = []

	for cand in candidates:
		print('Candidate', cand)
		worlds = []
		for i in range(len(trials)):
			print('Clip', i)
			tr = trials[i]

			alternatives = trial_alternatives[i] - {cand}

			rep = aspect_rep(tr, cand, 'B', alternatives, noise_val, perturb=0.01, num_samples=num_samples)

			worlds.append({"candidate": cand, "trial": i, "rep": rep})

		aspect_reps.append(worlds)

		print()


	with open(aspect_file_name, 'w+') as f:
		json.dump(aspect_reps, f, indent=4)




def sum_square(a, b): return np.sum((a-b)**2)

def load_trials(path):
	with open(path) as f:
		data_str = f.read()

	return json.loads(data_str)
