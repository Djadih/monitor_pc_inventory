import time
import praw
import webhooks
import configparser
import string

subreddits = []
keywords = [[]]
blacklist = []
lastPostTitles = []
userCount = 0
ignore = False


def load_reddit_data():
    global parser
    parser = configparser.ConfigParser()
    parser.read("config.ini")

    global subreddits
    subreddits = str(parser["REDDIT"]["subreddits"]).split(",")
    global keywords
    keywords = [x.split(",") for x in str(parser["REDDIT"]["keywords"]).split("|")]
    global userCount
    userCount = len(keywords)
    global blacklist
    blacklist = str(parser["REDDIT"]["blacklist"]).split(",")

    print("Subs to check:")
    print(subreddits)
    print("Keywords To Search For:")
    print(keywords)
    print("blacklisted Words:")
    print(blacklist)
    print("userCount:")
    print(userCount)


def return_reddit_instance(path_to_config_file):
    # get config options
    parser = configparser.ConfigParser()
    parser.read(path_to_config_file)
    client_id = str(parser["REDDIT"]["client_id"])
    client_secret = str(parser["REDDIT"]["client_secret"])
    user_agent = str(parser["REDDIT"]["user_agent"])

    load_reddit_data()

    reddit = praw.Reddit(
        client_id=client_id, client_secret=client_secret, user_agent=user_agent
    )

    return reddit


def check_keywords(submission, userIndex):
    submission_title = submission.title

    translator = str.maketrans(dict.fromkeys(string.punctuation))
    submission_title = submission_title.translate(translator)

    submission_words = str.lower(submission_title).split()

    global keywords
    global blacklist
    if any(word in keywords[userIndex] for word in submission_words):
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


def send_notification(submission, userIndex):
    print("Found:", submission.title)

    isNew = True
    global lastPostTitles
    global ignore
    if submission.title in lastPostTitles:
        isNew = False
    else:
        ignore = False

    try:
        webhooks.send_discord(
            submission.title + "\n" + submission.url, isNew, userIndex
        )
    except:
        pass


def check_continuous(scrape_delay, age_cutoff):
    count = scrape_delay
    found_count = 0
    global ignore
    while 1:
        try:
            if count % 5 == 0:
                print("Refreshing keywords/blacklist...")
                load_reddit_data()
            if count - found_count >= scrape_delay:
                submissions = get_submissions()
                curPostTitles = []
                for sub in submissions:
                    curPostTitles.append(sub.title)
                    for userIndex in range(0,userCount):
                        if check_keywords(sub,userIndex):
                            age = check_age(sub)
                            if age <= age_cutoff and ignore == False:
                                # if the post is recent, send notifications asap
                                # TODO: send notifications at a reduced rate (rather than stopping) if the post is old
                                send_notification(sub, userIndex)
                global lastPostTitles
                lastPostTitles = curPostTitles
            #Refresh .ini without actually having to stop and start

            print(count)
            count += 1
            time.sleep(scrape_delay)
        except:
            prompt = str.lower(input("Continue and mute current post?"))
            if prompt != "y":
                raise
            ignore = True
            pass

if __name__ == "__main__":

    reddit = return_reddit_instance("config.ini")

    input("Press Enter to continue... (We'll send a test message to start)")
    for userIndex in range(0, userCount):
        webhooks.send_discord(
            "Bot Starting Up:\nMonitoring Subreddits: "
            + str(subreddits)
            + "\nUsing Keywords: "
            + str(keywords[userIndex])
            + "\nBlacklist: "
            + str(blacklist)
            + "\nHappy Hunting!",
            True,
            userIndex,
        )
    # reasonable values are 5, 900
    check_continuous(5, 900)
