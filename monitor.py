import time
import praw
import webhooks
import configparser


def return_reddit_instance(path_to_config_file):
    # get config options
    parser = configparser.ConfigParser()
    parser.read(path_to_config_file)
    client_id = str(parser["REDDIT"]["client_id"])
    client_secret = str(parser["REDDIT"]["client_secret"])
    user_agent = str(parser["REDDIT"]["user_agent"])

    reddit = praw.Reddit(
        client_id=client_id, client_secret=client_secret, user_agent=user_agent
    )

    return reddit


def check_keywords(submission):
    keywords = {
        "nvidia",
        "rtx",
        "3070",
        "amd",
        "ryzen",
    }

    blacklist = {
        "prebuilt",
        "laptop",
        "monitor",
    }

    submission_title = submission.title

    # TODO: remove punctuation before splitting
    submission_words = str.lower(submission_title).split()

    if any(word in keywords for word in submission_words):
        if not any(word in blacklist for word in submission_words):
            return True
    return False


def check_age(submission):
    return (int)(time.time() - submission.created_utc)


def get_submission():
    submissions = reddit.subreddit("buildapcsales").new(limit=1)
    # submissions is a generator, so just get the first one and return it
    for submission in submissions:
        return submission


def send_notification(submission):
    print("Found:", submission.title)
    try:
        webhooks.send_discord(submission.title + "\n" + submission.url)
    except:
        pass


def check_continuous(scrape_delay, age_cutoff):
    count = scrape_delay
    found_count = 0

    while 1:
        if count - found_count >= scrape_delay:
            submission = get_submission()

            if check_keywords(submission):
                age = check_age(submission)
                if age <= age_cutoff:
                    # if the post is recent, send notifications asap
                    # TODO: send notifications at a reduced rate (rather than stopping) if the post is old
                    send_notification(submission)

        print(count)
        count += 1
        time.sleep(scrape_delay)


if __name__ == "__main__":

    reddit = return_reddit_instance("config.ini")

    # reasonable values are 5, 900
    check_continuous(5, 900)
