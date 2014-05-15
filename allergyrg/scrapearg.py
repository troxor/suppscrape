#!/usr/bin/env python 

import argparse
import bs4
import os
import re
from shutil import copy2
import sys
import time
from urllib import urlretrieve

from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--outfile", metavar="outfile", nargs="?", help="Write csv file")
args = parser.parse_args()

cachebase = os.environ['PWD']+"/cache/"
baseurl = "http://www.allergyresearchgroup.com/"

def scrape(itemid):
	
	filename = cachebase+str(itemid)+'.html'
	print " -scraping",filename
	soup = bs4.BeautifulSoup(open(filename).read())

	productcode = "ARG"+itemid
#	try:
#		producttypes = [x.string for x in soup.find("div", "sizes-available").find_all("li")]
#	except AttributeError:
#		producttypes = []
	productname = soup.find("div", {"class": "DialogTitle"}).text
	f = re.match('(.+)#', productname)
	prodname = f.group(1)

	description = soup.find("div", {"class": "xboxcontent"}).find("p").text
#	descripshort = soup.find("div", class_="short-description").text.strip()
	descripshort = description[0:40]+"..."
#	try:
#		description = soup.find("div", class_="gendesc").text
#	except AttributeError:
#		description = ""
	category = "1821,1868"
#	ingredients = ""
	try: 
		ingredients = soup.find("table", {"class": "ingredtbl"}).get_text()
	except AttributeError:
		ingredients = ""
#	for i in soup.find_all(class_='label-name'):
#		ingredients += i.text
#		try:
#			j = i.next_sibling
#			ingredients +=" "+j.text
#		except AttributeError:
#			pass
#		ingredients += "\n"
	# Grab the popup with the big image
	testurl = soup.find("td", {"align": "center", "valign": "top"}).a['onclick']
	t = re.search("window.open\('(/[^']+)',.+\)", testurl)
	realimgurl = baseurl+t.group(1)
	thumbpop = cachebase+itemid+"-popup.html"
	try:
		os.stat(thumbpop)
	except OSError:
		print "  -fetching popup"
		urlretrieve(realimgurl, filename=thumbpop)
	soup2 = bs4.BeautifulSoup(open(thumbpop).read())
	realimgurl = soup2.find("div", {"align": "center"}).find("img")["src"]
	print "  -found realimgurl",realimgurl
	url = baseurl+realimgurl

	product = [ productcode,
		    prodname,
		    descripshort,
		    description,
		    ingredients,
		    category,
		    url
		  ]
	genthumbs(productcode, url)
	return product

# end scrape
	
def genthumbs(prodcode, url):
	imgloc = cachebase+prodcode+".jpg"
	print " -genthumbs for",prodcode,":",url,"->",imgloc
	# download the image if needed
	
	try:
		os.stat(imgloc)
	except OSError:
		print "  -caching",imgloc
		urlretrieve(url, filename=imgloc)
	# Generate thumbnails if needed
	sizes = [("-0", 100), ("-1", 200)]
	for label, ysz in sizes:
		thumbloc = cachebase+prodcode+label+".jpg"
		try:
			os.stat(thumbloc)
		except OSError:
			print "  -shrinking thumb", thumbloc
			im = Image.open(imgloc)
			im.thumbnail((999,ysz), Image.ANTIALIAS)
			im.save(thumbloc, "JPEG")
	copies = [("-2T", 300), ("-2", 300)] # dimension not needed, just for reference
	for label, ysz in copies:
		copyloc = cachebase+prodcode+label+".jpg"
		try:
			os.stat(copyloc)
		except OSError:
			print "  -copying thumb", copyloc
			copy2(imgloc, copyloc)			


if __name__ == "__main__":

	try:
		os.stat(cachebase)
	except OSError:
		print "Creating cache dir",cachebase
		os.mkdir(cachebase)
	# Parse index page for all product page links

	# curl -o idx.html http://www.allergyresearchgroup.com/A-Z-Product-Names-sp-56.html
	soup = bs4.BeautifulSoup(open("idx.html").read())
	links = []
	print "Grabbing (itemid,prodpglinks) out of index page"
	for td in soup.find_all("td", {"class": "lftrtaz"}):
		try:
			td.a.span.decompose()
			tdid = td.a.text.strip(' ')
			if tdid[0] != "#":
				continue
			tdid = tdid[1:6]
			if td.a['href'][0:4] == "http":
				if "allergyresearchgroup.com" in td.a['href']:
					links.append( (tdid,td.a['href']) )
			else:
				links.append( (tdid, baseurl+td.a['href']) )
		except:
			pass

	# Fetch each one to ${productID}.html if not exists

	print "Caching product pages to itemid.html"
	for itemid,link in links:   # remove the range for production
		htmldoc = cachebase + itemid+'.html'
		try:
			os.stat(htmldoc)
		except OSError:
			print " -caching item",itemid,"from",link,"to",htmldoc	
			urlretrieve(link, filename=htmldoc)

	# Now that the product pages are cached, scrape them

	print "Scraping product information from product pages"
	allprods = []
	for itemid,link in links:
		prod = scrape(itemid)
		if len(prod) != 0:
			allprods.append(prod)

	print allprods[0:5]

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
		o.close()
			


