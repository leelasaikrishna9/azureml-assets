"""A simple script which tests for proper installation and invokability of
Vowpal Wabbit Python wrapper.

The script is based on the following toturials:
* https://vowpalwabbit.org/tutorials/contextual_bandits.html

It demonstrates simple example of working with contextual bandits using Python.
Training data for this example are generated on the fly.
"""

from vowpalwabbit import pyvw
import random

# Vowpal Wabbit minimizes cost, so "rewards" should be negative
USER_LIKED_ARTICLE = -1.0
USER_DISLIKED_ARTICLE = 0.0


def get_reward(context, action):
    if context['user'] == 'Tom':
        if context['time_of_day'] == 'morning' and action == 'politics':
            return USER_LIKED_ARTICLE
        elif context['time_of_day'] == 'afternoon' and action == 'music':
            return USER_LIKED_ARTICLE
        else:
            return USER_DISLIKED_ARTICLE
    elif context['user'] == 'Anna':
        if context['time_of_day'] == 'morning' and action == 'sports':
            return USER_LIKED_ARTICLE
        elif context['time_of_day'] == 'afternoon' and action == 'politics':
            return USER_LIKED_ARTICLE
        else:
            return USER_DISLIKED_ARTICLE


# Mapper to Vowpal Wabbit format
def to_vw_format(context, actions, cb_label=None):
    if cb_label is not None:
        chosen_action, reward, prob = cb_label

    example_string = ""
    example_string += "shared |User user={} time_of_day={}".format(context["user"], context["time_of_day"])
    for action in actions:
        example_string += "\n"
        if cb_label is not None and action == chosen_action:
            example_string += "0:{}:{} ".format(reward, prob)
        example_string += "|Action article={} ".format(action)

    return example_string


# Sample from probability mass function
def sample_from_pmf(pmf):
    total = sum(pmf)
    scale = 1 / total
    pmf = [x * scale for x in pmf]

    draw = random.random()
    sum_prob = 0.0

    for index, prob in enumerate(pmf):
        sum_prob += prob
        if (sum_prob > draw):
            return index, prob


# Putting it together to select an action
def get_action(vw, context, actions):
    vw_text = to_vw_format(context, actions)
    pmf = vw.predict(vw_text)
    chosen_action_index, prob = sample_from_pmf(pmf)

    return actions[chosen_action_index], prob


# Simulation setup
users = ['Anna', 'Tom']
times_of_day = ['morning', 'afternoon']
actions = ['politics', 'sports', 'music', 'food', 'finance', 'health', 'camping']


def choose_user():
    return random.choice(users)


def choose_time_of_day():
    return random.choice(times_of_day)


def run_simulation(vw, num_iterations, do_learn=True):
    reward_sum = 0.0
    ctr = []

    for i in range(1, num_iterations + 1):
        user = choose_user()
        time_of_day = choose_time_of_day()

        context = {'user': user, 'time_of_day': time_of_day}
        action, prob = get_action(vw, context, actions)

        reward = get_reward(context, action)
        reward_sum += reward

        if do_learn:
            vw_format = vw.parse(to_vw_format(context, actions, (action, reward, prob)), pyvw.vw.lContextualBandit)
            vw.learn(vw_format)

        ctr.append(-1 * reward_sum / i)

    return ctr


# Training
if __name__ == '__main__':
    print('Starting training.')

    vw = pyvw.vw('--cb_explore_adf -q UA --quiet --epsilon 0.2')

    num_iterations = 500
    ctr = run_simulation(vw, num_iterations, True)

    print('Training completed!')
