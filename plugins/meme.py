from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageEnhance
from io import BytesIO
from os import path
import sys, os, requests, pyimgur, random
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
from googleapiclient.discovery import build

d = path.dirname(__file__)

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
GOOGLE_API_CX = os.environ['GOOGLE_MEME_CX_KEY']
IMGUR_CLIENT_ID = os.environ['IMGUR_API_KEY']

HASH_FONT_NAME = path.join(d, "fonts\Allura-Regular.ttf")
HASH_FONT_SIZE = 28
MAIN_FONT_NAME = path.join(d, "fonts\DejaVuSerifCondensed-Italic.ttf")
MAIN_FONT_SIZE = 32
WIDTH_PERCENT = 0.80
HEIGHT_PERCENT = 0.40
OPACITY = 0.6
MAX_DEFAULT_MEMES = 1
IMAGE_FILE_NAME = path.join(d, 'meme/meme.png')

words_response = requests.get("http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain")
WORDS = words_response.content.splitlines()

last_text = ""

def reduce_opacity(im, opacity):
    """
    Returns an image with reduced opacity.
    Taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/362879
    """
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

def meme_image(img, mainText, hashText):
    # Figure out the image/text dimensions
    draw = ImageDraw.Draw(img)
    W, H = img.size
    hashfont = ImageFont.truetype(HASH_FONT_NAME, HASH_FONT_SIZE)
    ws, hs = draw.textsize(hashText, font=hashfont)
    fsize = MAIN_FONT_SIZE
    font = ImageFont.truetype(MAIN_FONT_NAME, fsize)
    w, h = draw.textsize(mainText, font=font)
    while w > (W * WIDTH_PERCENT) or h > (H * HEIGHT_PERCENT):
        fsize -= 1
        font = ImageFont.truetype(MAIN_FONT_NAME, fsize)
        w, h = draw.textsize(mainText, font=font)
    # Draw the transparent rectangles
    opaclayer = Image.new("RGBA", (W,H), (0,0,0,0))
    opacdraw = ImageDraw.Draw(opaclayer)
    opacdraw.rectangle(((W-w)/2,(H-h)/2,(W-w)/2 + w,(H-h)/2 + h), fill='black')
    opacdraw.rectangle((W-ws,H-hs,W,H), fill='black')
    opaclayer = reduce_opacity(opaclayer, OPACITY)
    img = Image.composite(opaclayer, img, opaclayer)
    # Draw the text onto the image
    draw = ImageDraw.Draw(img)
    draw.text(((W-w)/2,(H-h)/2), mainText, fill='white', font=font)
    draw.text((W-ws,H-hs), hashText, fill='white', font=hashfont)
    # Return the image
    return img

def find_image(query):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    num_attempts = 10
    
    try:
        res = service.cse().list(q=query, searchType='image', imgSize='large', imgType='photo', safe="high", cx=GOOGLE_API_CX, num=num_attempts).execute()    
    except:
        print("Something went wrong with a google search")
    
    #im = pyimgur.Imgur(IMGUR_CLIENT_ID)
    #item = im.search_gallery("tag: " + query.replace(" ", " OR "))
    
    attempt = 0
    while (attempt < num_attempts):        
        try:
            #if item[attempt].is_album:
            #    url = item[attempt].images[0].link
            #else:
            #    url = item[attempt].link
            #print(url)
            #response = requests.get(url)
            url = res['items'][attempt]['link']
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img.thumbnail((960,720), Image.ANTIALIAS)
            # log the image url so we can figure out bad domains for images
            try:
                log = open(path.join(d, 'meme\\log.txt'), 'a')
                log.write(url+ "\r\n")
                log.close()
            except:
                print("Logging Failed")
            break
        except:
            attempt += 1
        
    # Fallback to local images for the meme instead
    if attempt == num_attempts:
        img = Image.open(path.join(d, 'meme\\' + str(random.randint(1,MAX_DEFAULT_MEMES)) + '.jpg'))
        img.thumbnail((960,720), Image.ANTIALIAS)
        
    return img
    
def generate_meme(query, text, hash):
    img = find_image(query)
    if img == None:
        return False
    img = meme_image(img, text, hash)
    img.save(IMAGE_FILE_NAME)
    return True
    
def random_words(num):
    words = ""
    while num > 0:
        words += " " + str(random.choice(WORDS))[2:-1]
        num -= 1
    return words

def request_meme(text, channel, user):
    
    text_words = text.split(" ")
    if len(text_words) == 1 or not text_words[-1].startswith("#"):
        return ""
    
    hash = text_words[-1]
    words = random_words(2)
    query = text_words[-1].strip("#") + words
    del text_words[-1]
    message = " ".join(text_words)
    result = generate_meme(query, message, hash)
    if (result):
        im = pyimgur.Imgur(IMGUR_CLIENT_ID)
        item = im.upload_image(IMAGE_FILE_NAME)
        return item.link + " (" + words[1:] + ")"
    else:
        return ""
        
def create_meme_from_last_text(text, channel, user):
    global last_text
    
    if not text.startswith("#") or len(text.split(" ")) != 1:
        return ""
        
    message = last_text
    hash = text
    words = random_words(2)
    query = text.strip("#") + words
    
    result = generate_meme(query, message, hash)
    if (result):
        im = pyimgur.Imgur(IMGUR_CLIENT_ID)
        item = im.upload_image(IMAGE_FILE_NAME)
        return item.link + " (" + words[1:] + ")"
    else:
        return ""

def random_meme(text, channel, user):
    global last_text
    if not text.startswith('#'):
        last_text = text
    return ""
 #   if random.randint(1,100) > 2:
 #       return
 #   text = trigger.group(1)
 #   hash = "#just" + trigger.nick + "things"
 #   query = GetRandomWords(random.randint(2,3))[1:]
 #   result = GenerateMeme(query, text, hash)
 #   
 #   if (result):
 #       im = pyimgur.Imgur(IMGUR_CLIENT_ID)
 #       item = im.upload_image(IMAGE_FILE_NAME)
 #       bot.say(item.link + " (" + query + ")")

