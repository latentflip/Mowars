import urllib

def get_twitpic_image(image_str):
    url = 'http://twitpic.com/show/full/'+str(image_str)+'.jpg'
    response = urllib.urlopen(url)
    return response.read()