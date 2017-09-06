import shelve

POINTS_SHELF = 'points.shelf'

user_id_map = {'U4S3JCUF4': 'galnix', 
          'U4QMUNC8G': 'comptroller', 
          'U4S3A1Z4P': 'fazjaxton', 
          'U5BGCL405': 'frank', 
          'U4RSHS8FN': 'raptor'}

def change_points(word, change):
    shelf = shelve.open(POINTS_SHELF)
    try:
        points = shelf[word]
    except KeyError:
        points = 0
    points += change
    shelf[word] = points
    shelf.close()
    return points
    
def format_response(word, points):
    response = word + " has " + str(points)
    if points == 1:
        response += " point."
    else:
        response += " points."
    return response

def handle(command, channel, user):
    """
        Handles giving points to a user or word.
    """
    words = command.lower().split(" ")
    response = ""
    for word in words:
        if word.endswith("++"):
            # TODO if user is frank, have him say some stuff
            word = word.strip("-+")
            if word.startswith('<@'):
                try:
                    temp = word[2:].strip('>').upper()
                    temp = user_id_map[temp]
                except:
                    temp = ""
                if temp != "":
                    word = temp
            if user_id_map[user] == word:
                response = "Nice try."
            elif word == 'c' or word == 'C':
                response = ""
            else:
                points = change_points(word, 1)
                response = format_response(word, points)
        elif word.endswith("--"):
            # TODO if user is frank, have him say some stuff
            word = word.strip("-+")
            points = change_points(word, -1)
            response = format_response(word, points)
        elif word.endswith("+-") or word.endswith("-+"):
            word = word.strip("-+")
            points = change_points(word, 0)
            response = format_response(word, points)
    return response
	