import discord
from discord import app_commands
from discord.ext import commands

import PIL
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
import emoji

# hotfixed pil (font.size if hasattr(font,'size') else font.font.size)

import os

TOKEN = os.environ['your_bot_token_here']

PARAM_NUM = 11

HASH_DELIM = '.:.'
REPLY_DELIM = ','
BREAK_DELIM = '\n'
LINE_WIDTH = 1
WIDEFIT = 1
MIDFIT = 0.6

bot = commands.Bot(
	command_prefix='/',
	intents=discord.Intents.default()
)

@bot.event
async def on_ready():
	try:
		synced = await bot.tree.sync()
		print(f"synced {len(synced)} command(s)")
	except Exception as e:
		print(e)

@bot.event
async def on_message(interaction):
	if interaction.author.id == bot.user.id:
		return

	if interaction.reference and interaction.channel:
		target = await interaction.channel.fetch_message(
			interaction.reference.message_id
		)
		if target.author.id == bot.user.id:
			try:
				
				if interaction.content in ['delete', 'd']:
					await target.delete()
	
				else:
					amends = await tohash(interaction.content)
					if amends == False:
						await interaction.author.send(
							"syntax: x label"+REPLY_DELIM+" y spaced label"
						)
					
					else:
						hash = await amendhash(target.content, amends)
						await tofile(hash)
						with open('diagram.png', 'rb') as f:
							await interaction.channel.send(
								hash,
								file=discord.File(f)
							)
							
			except Exception as e:
				await interaction.author.send(e)

@bot.tree.command(name='tbt')
@app_commands.describe(
	hash = "🗺️.:.⏱️.:.🏞️.:.🏬.:.🌜.:.🌞.:.🌇.:.🌄.:.🌌.:.🌃.:.🥱",
	_x = "x coordinate",
	_y = "y coordinate",
	_xn = "when x is - (left)",
	_xp = "when x is + (right)",
	_yn = "when y is - (down)",
	_yp = "when y is + (up)",
	_1 = "1st quadrant",
	_2 = "2nd quadrant",
	_3 = "3rd quadrant",
	_4 = "4th quadrant",
	_t = "title of diagram",
	_pub = "True = publish, otherwise by default only you can see the bot reply",
	#add some more ...
)
async def tbt(interaction:discord.Interaction,
							hash:str=None,
								_x:str="",
								_y:str="",
								_xn:str="",
								_xp:str="",
								_yn:str="",
								_yp:str="",
								_1:str="",
								_2:str="",
								_3:str="",
								_4:str="",
								_t:str="",
							_pub:bool=False
						 	):
	try:
								
		hash = await tohash(hash)
		if hash == False:
			await interaction.response.send_message(
				"incorrect format ... or a bug?",
				ephemeral=True
			)
	
		else:
			hash = await amendhash(hash, [_x, _y, _xn, _xp, _yn, _yp, _1, _2, _3, _4, _t])
			await tofile(hash)
			# send to discord
			with open('diagram.png', 'rb') as f:
				await interaction.response.send_message(
					hash if _pub == True else hash + " (publish with _pub)",
					file = discord.File(f),
					ephemeral = not _pub
				)

	except Exception as e:
		await interaction.author.send(e)
	

#### utility

options = [
	'_x','_y','_xn','_xp','_yn','_yp','_1','_2','_3','_4','_t',
	'x','y','xn','xp','yn','yp','1','2','3','4','t'
]



async def tohash(hash):
	if hash is None:
		return hash
	
	cuts = hash.split(REPLY_DELIM)
	if len(cuts) == 1 and len(hash.split(HASH_DELIM)) > 1:
		if len(hash.split((HASH_DELIM))) == PARAM_NUM:
			return hash
		return False
		
	processed = {}
	for cut in cuts:
		c = cut.strip(" ").split(" ")
		if len(c) == 1 or c[0] not in options:
			return False
		else:
			key = options.index(c[0]) % PARAM_NUM
			if key in processed.keys():
				processed[key] += BREAK_DELIM + " ".join(c[1:])
			else:
				processed[key] = " ".join(c[1:])

	hash = ""

	keys = list(processed.keys())
	values = list(processed.values())
	for i in range(PARAM_NUM):
		if i in processed.keys():
			hash += values[keys.index(i)]
		if i != PARAM_NUM - 1:
			hash += HASH_DELIM
	
	return hash


async def amendhash(hash=None, hash2=None):
	if hash2 == None:
		return hash
	if hash == None:
		if isinstance(hash2, list):
			return HASH_DELIM.join(hash2)
		else:
			return hash2
	if not isinstance(hash2, list):
		hash2 = hash2.split(HASH_DELIM)
		
	for i, keep in enumerate(hash.split(HASH_DELIM)):
		if hash2[i] == "":
			hash2[i] = keep
	return HASH_DELIM.join(hash2)


async def tofile(hash):
	[_x, _y, _xn, _xp, _yn, _yp, _1, _2, _3, _4, _t] = hash.split(HASH_DELIM)

	## draw
								
	width = 800
	height = 800
	ox = width/2
	oy = height/2
	q1x = ox + (width-ox)/2
	q1y = oy - (height-oy)/2
	q2x = ox - (width-ox)/2
	q2y = q1y
	q3x = q2x
	q3y = oy + (height-oy)/2
	q4x = q1x
	q4y = q3y

	
	# images
	image = Image.new('RGB', (width, height), color='white')
	
	# draws
	draw = ImageDraw.Draw(image)
	
	# fonts
	font = ImageFont.truetype('LDFComicSans.ttf', 32)
	font90 = ImageFont.TransposedFont(font, Image.ROTATE_90)

	# utilities
	def getw(target):
		return font.getlength(
			emoji.replace_emoji(target, '   ')
		)

	def geth(target):
		return font.getbbox(target)[3]
	
	def drawtextdefault(xy, text, font=font):
		with Pilmoji(image) as pilmoji:
			pilmoji.text((int(xy[0]), int(xy[1])), text, font=font, fill="black")

	def drawprose(xy, text, wrapsize, anchor, font=font):
		wrap = []
		size = 0
		lasti = 0
		for i in range(len(text)):

			if text[i] == '\n':
				size += wrapsize
				text = text.replace('\n', ' ')
			
			if size + getw(text[i]) < wrapsize:
				size += getw(text[i])
				
			elif text[i+1] == " ":
				size += getw(text[i])
				
			else:
				if len(text[lasti:i].strip(" ").split(" ")) < 2:
					wrap.append(text[lasti:i].strip(" "))
					lasti = i
				else:
					append = " ".join(text[lasti:i].strip(" ").split(" ")[:-1])
					wrap.append(append)
					lasti = lasti + len(append)
				size = 0
		wrap.append(text[lasti:].strip(" "))

		
		lh = geth(text)
		x, y = {'h-': xy,
						'h0': (xy[0], xy[1] - lh*len(wrap)/2),
						'h+': (xy[0], xy[1] - lh*len(wrap)),
						'v-': xy,
						'v0': (xy[0] - lh*len(wrap)/2, xy[1]),
						'v+': (xy[0] - lh*len(wrap), xy[1])
					 } [anchor[0] + anchor[2]]
		for i in range(len(wrap)):
			drawtextdefault({
				'h+': (x, y + lh*i),
				'h0': (x - getw(wrap[i])/2, y + lh*i),
				'h-': (x - getw(wrap[i]), y + lh*i),
				'v+': (x + lh*i, y - getw(wrap[i])),
				'v0': (x + lh*i, y - getw(wrap[i])/2),
				'v-': (x + lh*i, y)
				} [anchor[0] + anchor[1]], wrap[i], font=font)
		pass
		
	def drawline(xy):
		draw.line(xy, fill='black')


	#should replace drawing functions with identification and draw after effecient shape is calculated

	#objects
	
	drawprose((q1x, q1y), _1, (width-ox) * MIDFIT, 'h00')
	drawprose((q2x, q2y), _2, (ox) * MIDFIT, 'h00')
	drawprose((q3x, q3y), _3, (ox) * MIDFIT, 'h00')
	drawprose((q4x, q4y), _4, (width-ox) * MIDFIT, 'h00')


	#morphisms
	
	if (_xn != ''):
		drawline((0, oy, ox - LINE_WIDTH/2, oy))
		drawprose((0, oy), _xn, ox * MIDFIT, 'h++')

	if (_xp != ''):
		drawline((ox - LINE_WIDTH/2, oy, width, oy))
		drawprose((width, oy), _xp, (width-ox) * MIDFIT, 'h-+')
	
	if (_yn != ''):
		drawline((ox - LINE_WIDTH/2, height, ox - LINE_WIDTH/2, oy))
		drawprose((ox, height), _yn, (width-ox) * MIDFIT, 'h++')
	
	if (_yp != ''):
		drawline((ox - LINE_WIDTH/2, oy, ox - LINE_WIDTH/2, 0))
		drawprose((ox, 0), _yp, (width-ox) * MIDFIT, 'h+-')	


	#functors 
	
	drawprose((q1x, oy), _x, (width-ox) * WIDEFIT, 'h0-')
	drawprose((ox, q1y), _y, (oy) * WIDEFIT, 'v0+', font90)
	
	
	#most efficient shape

	

	# draw title
	drawprose((0, 0), _t, ox * MIDFIT, 'h+-')
	
	# save image
	image.save('diagram.png')

bot.run(TOKEN)





""" gpt preliminary
import math

def draw_objects(L):
    # place objects in a circular pattern
    for i in range(L):
        angle = 2 * math.pi * i / L
        place_object(math.cos(angle), math.sin(angle))

def draw_morphisms(M, L):
    # create a list of all possible object pairs
    object_pairs = list(combinations(range(L), 2))
    # sort the pairs by the distance between objects
    object_pairs.sort(key=lambda pair: abs(pair[0] - pair[1]))
    # draw morphisms between the first M object pairs
    for i in range(M):
        draw_morphism(object_pairs[i])

def draw_functors(N, M):
    # assign each functor to a morphism
    for i in range(N):
        assign_functor_to_morphism(i % M, i)

def draw_graph(L, M, N):
    draw_objects(L)
    draw_morphisms(M, L)
    draw_functors(N, M)

"""