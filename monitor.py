import time
import praw
import webhooks
import configparser

subreddits = []
keywords = []
blacklist = []
lastPostTitles = []

def return_reddit_instance(path_to_config_file):
    # get config options
    parser = configparser.ConfigParser()
    parser.read(path_to_config_file)
    client_id = str(parser["REDDIT"]["client_id"])
    client_secret = str(parser["REDDIT"]["client_secret"])
    user_agent = str(parser["REDDIT"]["user_agent"])

    global subreddits
    subreddits = str(parser["REDDIT"]["subreddits"]).split(',')
    global keywords
    keywords = str(parser["REDDIT"]["keywords"]).split(',')
    global blacklist
    blacklist = str(parser["REDDIT"]["blacklist"]).split(',')

    print("Subs to check:")
    print(subreddits)
    print("Keywords To Search For:")
    print(keywords)
    print("blacklisted Words:")
    print(blacklist)

    reddit = praw.Reddit(
        client_id=client_id, client_secret=client_secret, user_agent=user_agent
    )

    return reddit


def check_keywords(submission):
    submission_title = submission.title

    # TODO: remove punctuation before splitting
    submission_words = str.lower(submission_title).split()

    global keywords
    global blacklist
    if any(word in keywords for word in submission_words):
        if not any(word in blacklist for word in submission_words):
            print("got one")
            return True
    return False


def check_age(submission):
    return (int)(time.time() - submission.created_utc)


def get_submissions():
    submissions_all = []
    global subreddits

    for sub in subreddits:
        submissions = reddit.subreddit(sub).new(limit=1)
        # submission is a generator, so just get first from each subreddit
        for submission in submissions:
            submissions_all.append(submission)
    print(submissions_all)
    return submissions_all


def send_notification(submission):
    print("Found:", submission.title)


    isNew = True
    global lastPostTitles
    if submission.title in lastPostTitles:
        isNew = False

    try:
        webhooks.send_discord(submission.title + "\n" + submission.url, isNew)
    except:
        pass


def check_continuous(scrape_delay, age_cutoff):
    count = scrape_delay
    found_count = 0

    while 1:
        if count - found_count >= scrape_delay:
            submissions = get_submissions()
            curPostTitles = []
            for sub in submissions:
                curPostTitles.append(sub.title)
                if check_keywords(sub):
                    age = check_age(sub)
                    if True or age <= age_cutoff:
                        # if the post is recent, send notifications asap
                        # TODO: send notifications at a reduced rate (rather than stopping) if the post is old
                        send_notification(sub)
            global lastPostTitles
            lastPostTitles = curPostTitles
        print(count)
        count += 1
        time.sleep(scrape_delay)


if __name__ == "__main__":

    reddit = return_reddit_instance("config.ini")

    input("Press Enter to continue... (We'll send a test message to start)")
    webhooks.send_discord("Bot Starting Up:\nMonitoring Subreddits: " + str(subreddits) + "\nUsing Keywords: " + str(keywords) + "\nBlacklist: " + str(blacklist) + "\nHappy Hunting!", True)
    # reasonable values are 5, 900
    check_continuous(5, 900)
