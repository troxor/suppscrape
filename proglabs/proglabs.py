#!/usr/bin/env python3
from __future__ import print_function
import string
import os
import sys
import argparse
from hashlib import md5

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Please install bs4 and requests.\n\n $ pip install beautifulsoup4 requests\n")
    exit(1)

baseurl="http://www.progressivelabs.com"

ALLPRODUCTS = {}

CACHEBASE="cache/"

LETTERS=[letter for letter in string.ascii_uppercase]
PCOUNTS=[3,3,4,2,1,1,3,1,2,0,1,2,3,1,2,4,1,1,1,2,1,1,1,0,0,1]

parser = argparse.ArgumentParser()
parser.add_argument('--write', action='store_true')
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()


def cachepg(basename, link):
    pg = CACHEBASE+basename+md5(link.encode()).hexdigest()+".html"
    try:
        os.stat(pg)
    except OSError:
        print(" -caching",pg)
        f = open(pg, 'w')
        s = requests.get(link).text
        f.write(s)
        f.close()
    return pg

def sancsv(string):
    return string.translate({ord(','):None, ord('\n'):None, ord('\"'):None}) or ""

def scrapeitemdetails(doup):

    details = {}

    # Description is just text, but strip newlines
    dets = " ".join([x for x in doup.find("div", attrs={"id": "productdescr"}).stripped_strings])
    details["descr"] = sancsv(dets)

    # Ingredients is an HTML table, strip attributes and whitespace
    ings = doup.find("table", attrs={"class": "ingTable"})
    if ings:
        ings.attrs = None
        for tag in ings.findAll(True):
            tag.attrs = None
        details["ingrd"] = sancsv("".join([str(x) for x in ings.contents]))
        return details
    
    # Ingredients could also be a div
    ings = doup.find("div", attrs={"id": "Ingredients"})
    if ings:
        ings.attrs = None
        for tag in ings.findAll(True):
            tag.attrs = None
        details["ingrd"] = sancsv("".join([str(x) for x in ings.contents]))
        return details

    details["ingrd"] = ""
    return details
    

def scrapeonepage(soup):
    
    for DBoxItem in soup.findAll("td", class_="DialogBox"):

            if len(list(DBoxItem.children)) <= 1:
                # Less than 12 items on this page, probably end of letter, ignore it
                break

            # Fetch key information: the unique id and link to product page
            id = DBoxItem.find("span", class_="smaller").contents[0][5:]
            plin = DBoxItem.find("a", class_="ProductTitle")
            plink = baseurl+"/"+plin['href']

            # Grab next "level" of item information
            dpg =  cachepg("plitem", plink)
            doup = BeautifulSoup(open(dpg).read())
            if args.verbose:
                print("   * scanning item:", plin)
            details = scrapeitemdetails(doup)

            # Massage relative links
            fimgl = DBoxItem.find("img", attrs={"height":"120"})['src']
            if fimgl[0] == '/':
                fimgl = baseurl+fimgl

            ALLPRODUCTS[id] = {
                    "link": plink,
                    "name": plin.text.translate({ord(','):None, ord('\n'):None}),
                    "imgl": fimgl,
                    "pric": DBoxItem.center.font.text[1:],
                    "skuu": "PLABS-"+str(id),
                    "dscr": details["descr"]+"<br/><br/>"+details["ingrd"]
                }
            if args.verbose:
                print(ALLPRODUCTS[id])

    return

############################################################

if __name__ == "__main__":

    # Scrape the pages

    for A in LETTERS:
        print("::",A,"::")
        for x in range(0,PCOUNTS[LETTERS.index(A)]):
            X = x+1
            print(" * scanning letter %s, page %d" % (A, X))

            prodpage=baseurl+"/home.php?letter="+A+"&page="+str(X)
            pg = cachepg("proglabs", prodpage)
            soup = BeautifulSoup(open(pg).read())
            scrapeonepage(soup)
        print("Total products found so far: "+str(len(ALLPRODUCTS)))

    # Output the results

    if args.write:
        outcsv = open("plabs-products.csv", 'w')
        # From sample
        outcsv.write("Handle,Title,Body (HTML),Vendor,Type,Tags,Published,Option1 Name,Option1 Value,Option2 Name,Option2 Value,Option3 Name,Option3 Value,Variant SKU,Variant Grams,Variant Inventory Tracker,Variant Inventory Qty,Variant Inventory Policy,Variant Fulfillment Service,Variant Price,Variant Compare At Price,Variant Requires Shipping,Variant Taxable,Variant Barcode,Image Src,Image Alt Text,Variant Img")

    print("\n\n - - - - - FINAL OUTPUT - - - - -")
    for k in sorted(ALLPRODUCTS.keys()):
        if args.verbose:
            print(" * Product "+str(k)+" = "+str(ALLPRODUCTS[k]))

        # CSV format (http://docs.shopify.com/manual/your-store/products/product-csv)
        csvline = [
                    ALLPRODUCTS[k]["skuu"],                 # Handle
                    ALLPRODUCTS[k]["name"],                 # Title
                    ALLPRODUCTS[k]["dscr"],                 # Body (HTML)
                    "Progressive Laboratories",             # Vendor
                    "Supplement",                           # Product Type
                    "",                                     # Tags
                    "FALSE",                                # Published (bool)
                    "Title", "Title",                       # Option1 Name, Option1 Value
                    "","",                                  # Option2 Name, Option2 Value
                    "","",                                  # Option3 Name, Option3 Value
                    "",                                     # Variant SKU
                    "0",                                    # Variant Grams
                    "",                                     # Variant Inventory Tracker
                    "1",                                    # Variant Inventory Quantity
                    "deny",                                 # Variant Inventory Policy
                    "manual",                               # Variant Fulfillment Service
                    ALLPRODUCTS[k]["pric"],                 # Variant Price
                    "",                                     # Variant Compare at Price
                    "",                                     # Variant Requires Shipping
                    "",                                     # Variant Taxable
                    "",                                     # Variant Barcode
                    ALLPRODUCTS[k]["imgl"],                 # Image Src
                    ALLPRODUCTS[k]["name"],                 # Image Alt Text
                    "FALSE",                                # Gift Card
                                # Metafields
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                  ]
        if args.write:
            outcsv.write( ",".join(csvline)+"\n" )
    if args.write:
        outcsv.close()

    print("Total products scraped:",len(ALLPRODUCTS), "\n\n")

