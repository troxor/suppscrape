#!/usr/bin/env python 

import argparse
import bs4
import os
import re
from shutil import copy2
import sys
from urllib import urlretrieve

from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--outfile", metavar="outfile", nargs="?", help="Write csv file")
parser.add_argument("infile", metavar="infile", nargs="+", help="Filename to scrape")
args = parser.parse_args()

def scrape(filename):
	
	print "Scraping",filename
	infile = open(filename).read()
	soup = bs4.BeautifulSoup(infile)

	productcodes = soup.find("p", class_="product-ids").text[12:].split(',')
	try:
		producttypes = [x.string for x in soup.find("div", "sizes-available").find_all("li")]
	except AttributeError:
		producttypes = []
	productname = soup.find("div", class_="product-name").find("h1").text
	descripshort = soup.find("div", class_="short-description").text.strip()
	try:
		description = soup.find("div", class_="gendesc").text
	except AttributeError:
		description = ""
	category = "1818,1836"
	ingredients = ""
	for i in soup.find_all(class_='label-name'):
		ingredients += i.text
		try:
			j = i.next_sibling
			ingredients +=" "+j.text
		except AttributeError:
			pass
		ingredients += "\n"
	imgurl = soup.find("p", class_="product-image").find("img")["src"]

	products = []
	for productcode in productcodes:
		if len(producttypes) != 0:
			productfullname = productname+" ("+producttypes[productcodes.index(productcode)]+")"
		else:
			productfullname = productname
		product = [ productcode.strip(),
			    productfullname,
			    descripshort,
			    description,
			    ingredients,
			    category,
			    imgurl
			  ]
		products.append(product)
	return products

# end scrape
	


if __name__ == "__main__":
	allprods = []
	for f in args.infile:
		prod = scrape(f)
		if len(prod) != 0:
			allprods+=prod

	if (args.outfile is None):
		for prod in allprods:
			print "###############"
			print "- Product ID: ", prod[0].encode('utf-8').strip()
			print "- Name:       ", prod[1].encode('utf-8').strip()
			print "- Short Desc: ", prod[2].encode('utf-8').strip()
			print "- Description:", prod[3].encode('utf-8').strip()
			print "- Ingredients:", prod[4].encode('utf-8').strip()
			print "- Category:   ", prod[5].encode('utf-8').strip()
			print "- Image URL:  ", prod[6].encode('utf-8').strip()
	else:
		o = open(args.outfile, "wb")
		o.write("productcode,productname,productdescriptionshort,productdescription,techspecs,categoryids\n")
		for prod in allprods:
			# Write to the CSV
			o.write('"'+'","'.join(prod[0:6]).encode('utf-8').strip()+'"\n')
			
			imgbase = os.environ["PWD"]+"/imgcache/"
			# Download the image if needed
			imgloc = imgbase+prod[0]+".jpg"
			try:
				os.stat(imgloc)
			except OSError:
				print " -caching",imgloc
				urlretrieve(prod[6], filename=imgloc)
			# Generate thumbnails if needed
			sizes = [("-0", 100), ("-1", 200)]
			for label, ysz in sizes:
				thumbloc = imgbase+prod[0]+label+".jpg"
				try:
					os.stat(thumbloc)
				except OSError:
					print "  -shrinking thumb", thumbloc
					im = Image.open(imgloc)
					im.thumbnail((999,ysz), Image.ANTIALIAS)
					im.save(thumbloc, "JPEG")
			copies = [("-2T", 300), ("-2", 300)] # dimension not needed, just for reference
			for label, ysz in copies:
				copyloc = imgbase+prod[0]+label+".jpg"
				try:
					os.stat(copyloc)
				except OSError:
					print "  -copying thumb", copyloc
					copy2(imgloc, copyloc)			
		
		o.close()
			
		
	sys.exit(0)

