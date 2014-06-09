from django.http import HttpResponse
from django.shortcuts import render
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
import urllib2
from BeautifulSoup import *
from urlparse import urljoin
import urllib
import time
import nltk
from collections import Counter
import sklearn.feature_extraction.text as fe
import networkx
import operator

articles = []

class story:

    def __init__(self,title,story,url,source):
        self.title = title
        self.permalink = url
        self.source = source
        self.article = ""
        
        for line in story:
            self.article = self.article + line

        while(1):
            startIndex = None
            endIndex = None
            
            if '(' in self.article:
                startIndex = self.article.index('(')

            if ')' in self.article:
                endIndex = self.article.index(')')

            if startIndex and endIndex:
                self.article = self.article[:startIndex] + self.article[endIndex+1:]
            elif startIndex:
                self.article = self.article[:startIndex] + self.article[startIndex+1:]
            elif endIndex:
                self.article = self.article[:endIndex] + self.article[endIndex+1:]
            else:
                break

        self.article.replace("&nbsp;","")
        
        
def crawlHinduArticle(link):
    
    global articles
    
    try:
        linkContent = getPage(link)
    except:
        print "Problem getting page. Connection issues"
        return
    
    linkSoup = BeautifulSoup(linkContent.read())
    print "crawling" , link
    
    try:
        titleString = linkSoup.find('h1').string
    except:
        titleString = ""
    
    articleBlock = linkSoup.find('div',id="article-block")
    
    for divs in articleBlock:
        try:
            if divs['class'] == "article-text":
                articleWrapper = divs
                print "div found"
                break
        except:
            continue
        
    article = ""
        
    for item in articleWrapper:
        try:
            if item.name == "p":
                print item
                if ('&#8220;' in item.string):
                    print "yes!"
                    
                article = article +  str(item.string.replace('&#8220;','"').replace('&#8221;','"').replace('\n','').replace('\r','').replace('\t',''))
               
        except:
            continue
        
    if article != "":
        storyObj = story(titleString,summarizeArticle(article),link,"The Hindu")
        articles.append(storyObj)
        
    return
        
     


def crawlNDTVMain(link):
    
    global articles
    
    try:
        linkContent = getPage(link)
    except:
        print "Problem getting Page. Connection issues."
        return
    
    linkSoup = BeautifulSoup(linkContent.read())
    print "crawling" , link
    div = linkSoup.find("div",id="in_main_story")

    tagsToRemove = []
    
    if div:
        titleString = linkSoup.find("h1").string

        print titleString
        
        for tag in div.findAll(True):
            if tag.parent == div:
               tagsToRemove.append(tag)

        for rem in tagsToRemove:
            s = ""
            if rem.name == "a":
                s = rem.string
            rem.replaceWith(s)
        
        article = ""
        
        for string in div.contents:
            if string != u'\n' and string != u'':
                article = article + string

        if article != "":
            storyObj = story(titleString,summarizeArticle(article),link,"NDTV")
            articles.append(storyObj)

def crawlNDTVsubDomains(link,domain):

    global articles
    
    try:
        linkContent = getPage(link)
    except:
        print "Problem getting Page. Connection issues."
        return

    linkSoup = BeautifulSoup(linkContent.read())
    print "crawling ", domain , link
    divs = linkSoup("div")

    if domain == "profit":
        className = "pdl200"
    elif domain == "sports":
        className = "art-body"

    internalLinks = []
    
    for div in divs:
        if ('class' in dict(div.attrs)) and domain != "gadgets":
            if (div['class'] == className):

                titleString = linkSoup.find("h1").string

                print titleString

                article = ""
                
                for tag in div.findAll(True):
                    if tag and tag.name == "p":
                        for item in tag.contents:
                            try:
                                if ('name' in dict(item.attrs)):
                                    if item['name'] == "a":
                                        internalLinks.append(item['href'])
                                        try:
                                            article = article + item.string
                                        except:
                                            if len(item.contents)==1:
                                               article = article + item.contents[0].string

                                    elif item['name'] == "strong":
                                        article = article + item.string

                            except:
                                article = article + str(item.replace('\n','').replace('\r','').replace('\t',''))

                                     
                                
                            
                
                if article != "":
                    storyObj = story(titleString,summarizeArticle(article),link,"NDTV")
                    articles.append(storyObj)


        elif ('id' in dict(div.attrs)):
            if (div['id'] == "HeadContent_FullstoryCtrl_fulldetails"):

                titleString = linkSoup.find("span",id="HeadContent_FullstoryCtrl_title").string

                print titleString

                article = ""
                
                for tag in div.findAll(True):
                    if tag and tag.name == "p":
                        for item in tag.contents:
                            try:
                                if ('name' in dict(item.attrs)):
                                    if item['name'] == "a":
                                        internalLinks.append(item['href'])
                                        try:
                                            article = article + item.string
                                        except:
                                            if len(item.contents)==1:
                                               article = article + item.contents[0].string

                                    elif item['name'] == "strong":
                                        article = article + item.string

                            except:
                                article = article + str(item.replace('\n','').replace('\r','').replace('\t',''))

                                     
                                
                            
                
                if article != "":
                    storyObj = story(titleString,summarizeArticle(article),link,"NDTV")
                    articles.append(storyObj)
 


def summarizeArticle(raw):
    #sentenceTokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    #sentTokens = sentenceTokenizer.tokenize(raw)
    sentTokens = raw.split('.')

    featureMatrix = fe.CountVectorizer().fit_transform(sentTokens)
    normalizedMatrix = fe.TfidfTransformer().fit_transform(featureMatrix)

    similarityGraph = normalizedMatrix*normalizedMatrix.T
    networkGraph = networkx.from_scipy_sparse_matrix(similarityGraph)
    scores = networkx.pagerank(networkGraph)

    sortedScores = sorted(scores.iteritems(), key=operator.itemgetter(1),reverse=True)

    selectedSentences = []

    if len(sortedScores)>= 2:
        upper = 2
    else :
        upper = len(sortedScores)

    
    
    for i in range(0,upper):
        selectedSentences.append(sortedScores[i][0])

    selectedSentences = sorted(selectedSentences)

    print len(sentTokens), len(sortedScores), len(selectedSentences)

    summary = []
    
    for index in selectedSentences:
        summary.append(sentTokens[index])


    return summary
    
def getPage(url):
    return urllib2.urlopen(url)


def crawlNDTV(response):

    global articles
    
    crawlURL = "http://www.thehindu.com"

    try:
        content = urllib2.urlopen(crawlURL)
    except:
        return HttpResponse("Connection Error")
    
    soup = BeautifulSoup(content.read())
    
    linksList = []
    
#### Getting top stories' links from The hindu's website
     
    mainLink = soup.find('h1').find('a')['href'].split("?")[0]
      
    linksList.append(mainLink)
      
    headingsDiv = soup.find('div',id="most-tab")
      
    for item in headingsDiv.contents:
        try:
            if ('class' in dict(item.attrs)):
                if (item['class'] == "tab1 tab"):
                    headings = item.findAll('h3')
        except:
            continue        
      
    for heading in headings:
          
        link = heading.find('a')['href'].split("?")[0]
        linksList.append(link)        
      

### getting top stories' links from NDTV's home page
#     divs = soup.findAll('div')
# 
#     linksList = []
# 
#     for div in divs:
#         if ('class' in dict(div.attrs)):
#             if (div['class'] == "topst_listing"):
#                 links = div.findAll('a')
# 
#                 for link in links:
#                     linksList.append(link['href'].split('?')[0])
# 
#                 break

    time.sleep(1)
##
    for link in linksList:
        
        crawlHinduArticle(link)
#   NDTV  
#    
#     for link in linksList:
#         
#         if link.split(".")[0] == "http://www" and "opinion" not in link:
#             crawlNDTVMain(link)
#                 
#         elif link.split(".")[0] == "http://profit" and "opinion" not in link:
#             crawlNDTVsubDomains(link,"profit")
# 
#         elif link.split(".")[0] == "http://sports" and "opinion" not in link:
#             crawlNDTVsubDomains(link,"sports")
# 
#         elif link.split(".")[0] == "http://gadgets" and "opinion" not in link:
#             crawlNDTVsubDomains(link,"gadgets")
# 
#             
            
                        
    return HttpResponse(linksList)


def home(response):
    global articles
    return render(response,"summarize.html",{"data":articles})


