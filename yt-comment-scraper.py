import argparse
import urllib
from urllib.parse import urlencode
from urllib.request import urlopen
import json


class YouTubeApi():

    YOUTUBE_COMMENTS_URL = 'https://www.googleapis.com/youtube/v3/commentThreads'
    comment_counter = 0

    def format_comments(self, results, likes_required):
        comments_list = []
        for item in results["items"]:
            comment = item["snippet"]["topLevelComment"]

            likes = comment["snippet"]["likeCount"]
            if likes < likes_required:
                continue

            author = comment["snippet"]["authorDisplayName"]
            text = comment["snippet"]["textDisplay"]

            str = "Comment by {}:\n \"{}\"\n\n".format(author, text)
            str = str.encode('ascii', 'replace').decode()

            comments_list.append(str)
            self.comment_counter += 1
            print("Comments downloaded:", self.comment_counter, end="\r")

        return comments_list


    def openURL(self, url, parms):
        url = url + '?' + urlencode(parms)
        with urlopen(url) as filehandle:
            data = filehandle.read()
        data = data.decode("utf-8")

        return data


    def get_video_comments(self, video_id, key, likes_required):
        parms = {
            'part': 'snippet,replies',
            'maxResults': 100,
            'videoId': video_id,
            'textFormat': 'plainText',
            'key': key
        }

        try:
            data = self.openURL(self.YOUTUBE_COMMENTS_URL, parms)
        except urllib.error.HTTPError as err:
            if err.getcode() == 400:
                exit("Invalid API key")
            elif err.getcode() == 404:
                print("URL not found")
                return
            elif err.getcode() == 403:
                print("Error: There are 2 possibilities:\n\
                    1.Video has disabled comments\n\
                    2.You don't have youtube API enabled. Enable it by visiting: https://console.developers.google.com/apis/library/youtube.googleapis.com\n\
                    If it still doesn't work than generate new key or create new project by visiting https://console.developers.google.com/apis/library/youtube.googleapis.com/credentials,\
                    switch to it and then generate new key")
                return
        except urllib.error.URLError:
            print("Cannot open URL at the moment")
            return

        results = json.loads(data)
        nextPageToken = results.get("nextPageToken")

        commments_list = []
        commments_list += self.format_comments(results, likes_required)

        while nextPageToken:
            parms.update({'pageToken': nextPageToken})
            data = self.openURL(self.YOUTUBE_COMMENTS_URL, parms)
            results = json.loads(data)
            nextPageToken = results.get("nextPageToken")
            commments_list += self.format_comments(results, likes_required)

        return commments_list


    def get_video_id_list(self, filename):
        try:
            with open(filename, 'r') as file:
                URL_list = file.readlines()
        except FileNotFoundError:
            exit("File \"" + filename + "\" not found")

        list = []
        for url in URL_list:
            if url == "\n":     # ignore empty lines
                continue
            if url[-1] == '\n':     # delete '\n' at the end of line
                url = url[:-1]
            if url.find('='):   # get id
                id = url[url.find('=') + 1:]
                list.append(id)
            else:
                print("Wrong URL")

        return list


def main():
    yt = YouTubeApi()

    parser = argparse.ArgumentParser(add_help=False, description=("Download youtube comments from many videos into txt file"))
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    required.add_argument("--key", '-k', help="Required API key you can get here: https://console.developers.google.com/apis/credentials")
    optional.add_argument("--likes", '-l', help="The amount of likes a comment needs to be saved", type=int)
    optional.add_argument("--input", '-i', help="URL list file name")
    optional.add_argument("--output", '-o', help="Output file name")
    optional.add_argument("--help", '-h', help="Help", action='help')
    args = parser.parse_args()

    # --------------------------------------------------------------------- #

    if not args.key:
        exit("Please specify API key using the -key parameter.")
    key = args.key

    likes = 0
    if args.likes:
        likes = args.likes

    input_file = "URL_list.txt"
    if args.input:
        input_file = args.input

    output_file = "Comments.txt"
    if args.output:
        output_file = args.output

    list = yt.get_video_id_list(input_file)
    if not list:
        exit("No URLs in input file")

    try:
        
        vid_counter = 0
        with open(output_file, "a") as f:
            for video_id in list:
                vid_counter += 1
                print("Downloading comments for video ", vid_counter, ", id: ", video_id, sep='')
                comments = yt.get_video_comments(video_id, key, likes)
                if comments:
                    for comment in comments:
                        f.write(comment)

        print('\nDone!')

    except KeyboardInterrupt:
        exit("User Aborted the Operation")

    # --------------------------------------------------------------------- #


if __name__ == '__main__':
    main()
