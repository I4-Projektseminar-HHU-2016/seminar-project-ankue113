#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import pprint
import nltk
import re

import urllib
import json

import sys

# sys.setdefaultencoding() does not exist, here!
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

bookPath="HP2.txt"


nppDictionary = {}

posDict = {}
neutralDict = {}
negDict = {}
countDict = {}

maxscale = 1
minscale = -1

with open(bookPath, "r") as f:
	rawcontent	= f.read()

	# sanitize '
	rawcontent = re.sub('\xe2\x80\x99', "'", rawcontent)

	# sanitize -
	rawcontent = re.sub('\xe2\x80\x94', '-', rawcontent)

	# sanitize ""
	rawcontent = re.sub('\xe2\x80\x9c', '\"', rawcontent)
	rawcontent = re.sub('\xe2\x80\x9d', '\"', rawcontent)

	rawcontent = re.sub('\. \. \.', '..."', rawcontent)

	# remove page number
	rawcontent = re.sub('\xc2\x91(.*?)\xc2\x91', '', rawcontent)

	# remove chapter
	rawcontent = re.sub('CHAPTER (ONE|TWO|THREE|FIVE|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN|FOUR|SIX)', '', rawcontent)

	# remove chapter title
	rawcontent = re.sub('(THE WORST BIRTHDAY|DOBBY\'S WARNING|THE BURROW|AT FLOURISH AND BLOTTS|THE WHOMPING WILLOW|GILDEROY LOCKHART|MUDBLOODS AND MURMURS|THE DEATHDAY PARTY|THE WRITING ON THE WALL|THE ROGUE BLUDGER|THE DUELING CLUB|THE POLYJUICE POTION|THE VERY SECRET DIARY|CORNELIUS FUDGE|ARAGOG|THE CHAMBER OF SECRETS|THE HEIR OF SLYTHERIN|DOBBY\'S REWARD)', '', rawcontent)

	#pprint.pprint("sentences:")
	sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
	sent = sent_detector.tokenize(rawcontent.strip())
	vari = 0
	
	sentcount = len(sent)
	lastpercent = -1;
	for i in sent:
		vari = vari + 1
		
		# process only X sentences
		#if vari >= 16: 
		#	break
		
		# calculate the percentage of processed sentences
		curpercent = int(float(vari)/float(sentcount)*float(100))
		if lastpercent < curpercent:
			lastpercent = curpercent
			percentstring = "Processing file (" + str(curpercent) + "%)"
			print(percentstring)
			sys.stdout.write('\033[F')
		
		#print("sentence " + str(vari) + ":")
		#pprint.pprint(i)
		tokens = nltk.word_tokenize(i)
		#print("tokens:")
		#pprint.pprint(tokens)
		#print("PoS:")
		postags = nltk.pos_tag(tokens)
		#pprint.pprint(postags)
		
		# get sentiment for this sentence
		#data = urllib.urlencode({"text": i}) 
		#u = urllib.urlopen("http://text-processing.com/api/sentiment/", data)
		#the_page = u.read()
		
		# query sentistrength website
		sentimentValue = 0
		params = urllib.urlencode({'text': re.sub('\W+', ' ', i), 'submit': 'Detect Sentiment', 'result': 'scale'})
		f = urllib.urlopen("http://sentistrength.wlv.ac.uk/results.php", params)
		rawhtml = f.read()
		# parse the response website and extract the scale value
		exsummary = re.search('<span class="\ExecutiveSummary\">(.*?)</span>', rawhtml)
		if exsummary:
			summaryscale = re.search('<b>(.*?)</b>', exsummary.group(1))
			if summaryscale:
				sentimentValue = int(summaryscale.group(1))
		
		# process only NNP
		for ptagseq in postags:
			if ptagseq[1] == 'NNP' and len(ptagseq[0]) >= 3:
				# increment name counter
				if ptagseq[0] in nppDictionary:
					nppDictionary[ptagseq[0]] += 1
				else:
					nppDictionary[ptagseq[0]] = 1
					
					
				#modify positive sentiment values
				if sentimentValue > 0:
					if ptagseq[0] in posDict:
						posDict[ptagseq[0]] += sentimentValue
					else:
						posDict[ptagseq[0]] = sentimentValue
					
					if not ptagseq[0] in neutralDict:
						neutralDict[ptagseq[0]] = 0
					if not ptagseq[0] in negDict:
						negDict[ptagseq[0]] = 0
				
				#modify neutral sentiment values				
				if sentimentValue == 0:
					if ptagseq[0] in neutralDict:
						neutralDict[ptagseq[0]] += sentimentValue
					else:
						neutralDict[ptagseq[0]] = sentimentValue
					
					if not ptagseq[0] in posDict:
						posDict[ptagseq[0]] = 0
					if not ptagseq[0] in negDict:
						negDict[ptagseq[0]] = 0
				
				#modify negative sentiment values		
				if sentimentValue < 0:
					if ptagseq[0] in negDict:
						negDict[ptagseq[0]] += sentimentValue
					else:
						negDict[ptagseq[0]] = sentimentValue
					
					if not ptagseq[0] in posDict:
						posDict[ptagseq[0]] = 0
					if not ptagseq[0] in neutralDict:
						neutralDict[ptagseq[0]] = 0
				
				#debug output for each increment
				print("'%s' pos:%d, neut:%d, neg:%d" % (ptagseq[0], posDict[ptagseq[0]], neutralDict[ptagseq[0]], negDict[ptagseq[0]] ))

maxnumber = 0		
# calculate max number for scaling purpose
for i in sorted(nppDictionary, key=nppDictionary.get):
	#print("%d×'%s'" % (nppDictionary[i], i))
	if nppDictionary[i] > maxnumber:
		maxnumber = nppDictionary[i]
#print("Maxnumber: " + str(maxnumber))


# calculate max and min values for positive/negative sentiment values
for i in sorted(nppDictionary, key=nppDictionary.get):
	print("%d×'%s' (%dpercent) pos:%d, neut:%d, neg:%d" % ( nppDictionary[i], i, float(nppDictionary[i])/float(maxnumber)*float(100), posDict[i], neutralDict[i], negDict[i] ))

	#calculate max and min scale values
	scale = negDict[i] + posDict[i]
	
	if scale > maxscale:
		maxscale = scale
	if scale < minscale:
		minscale = scale
		


# prepare json package
jsonData = 'json = { "nodes": ['
insertcount = 0

y = 0
maxsizescale = max(abs(minscale), abs(maxscale))

# iterate through all NNP entries and add them with the right color and translation to the json package
for i in sorted(nppDictionary, key=nppDictionary.get):
	if insertcount != 0:
		jsonData += ','
	insertcount += 1
	
	color = "#ffffff"
	x = 400
	
	
	scale = negDict[i] + posDict[i]
	if scale > 0:
		cval = int( (float(scale) / float(maxscale)) * float(255) )
		print("color" + str(cval))
		if cval > 255:
			cval = 255
		if cval < 0:
			cval = 033
		color = '#%02x%02x%02x' % (255-cval, 255, 255-cval)
		
		print("scale: " + str(scale))
		print("maxscale: " + str(maxscale))
		print("max:" +  str(int( (float(scale) / float(maxscale)) * float(300) )) )
		x = 400 + abs(int( (float(scale) / float(maxscale)) * float(300) ))
		
	if scale < 0:
		cval = int( (float(scale) / float(minscale)) * float(255) )
		print("color" + str(cval))
		if cval > 255:
			cval = 255
		if cval < 0:
			cval = 033
		color = '#%02x%02x%02x' % (255, 255-cval, 255-cval)
	
		print("scale: " + str(scale))
		print("minscale: " + str(minscale))
		x = 400 - abs(int( (float(scale) / float(minscale)) * float(300) ))
		print("min:" + str(int( (float(scale) / float(minscale)) * float(300) )) )
	
	#radius range between 40 and 80

	r = 40 + abs(int( (float(nppDictionary[i])/float(maxnumber)) * float(40) ))

	y += r
	label = i
	jsonData += '{"x":' + str(x) + ', "y":' + str(y) + ', "r":' + str(r) + ', "label":\"' + label + '\", "color":\"' + color + '\"}'
	
	y += r
	y += 4 #margin
	
# close the json package
jsonData += '] };'
#print(jsonData)

# website with the inserted json values
website = '<html><head><meta charset="UTF-8"><meta http-equiv="Content-Type" content="text/html;charset=utf-8"><script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js"></script><script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.9.1/jquery-ui.min.js"></script><script src="https://cdnjs.cloudflare.com/ajax/libs/d3/3.4.11/d3.min.js"></script><script language="javascript" type="text/javascript">'
website += '$( document ).ready(function() {var width = 800, height = 5000,'
website += jsonData
website += 'var svg = d3.select("body").append("svg") .attr("width", width) .attr("height", height);svg.append("defs") .append("pattern") .attr({ "id": "stripes", "width": "8", "height": "8", "fill": "red", "patternUnits": "userSpaceOnUse", "patternTransform": "rotate(60)" }) .append("rect");'
website += 'function plotChart(json) { /* Define the data for the circles */ var elem = svg.selectAll("g myCircleText") .data(json.nodes); /*Create and place the "blocks" containing the circle and the text */ var elemEnter = elem.enter() .append("g") .attr("class", "node-group") .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")" });'
website += '/*Create the circle for each block */ var circleInner = elemEnter.append("circle") .attr("r", function(d) { return d.r }) .attr("stroke", function(d) { return d.color; }) .attr("fill", function(d) { return d.color; }); var circleOuter = elemEnter.append("circle") .attr("r", function(d) { return d.r }) .attr("stroke", function(d) { return d.color; }) .attr("fill", "url(#stripes)"); /* Create the text for each block */ elemEnter.append("text") .text(function(d) { return d.label }) .attr({ "text-anchor": "middle", "font-size": 20, "fill" : "#000" , "dy": function(d) { return d.r / ((d.r * 25) / 100); } });};plotChart(json);});'
website += '</script><style>body{margin:0;padding:0;background-color:rgb(100,100,100);}.node-group { fill: #ffffff;}</style><body></body></html>'

# save visualization
text_file = open("visualization.html", "w")
text_file.write(website)
text_file.close()
