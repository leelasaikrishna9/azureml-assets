"""A simple script which tests for proper installation and availability of
Vowpal Wabbit command line.

The script is based on the following toturials:
* https://vowpalwabbit.org/tutorials/cmd_first_steps.html
* https://vowpalwabbit.org/tutorials/contextual_bandits.html

It demonstrates training and testing of a linear regression model and also
a simple example of working with contextual bandits.
In both cases training (and test) data are generated on the fly, and then
stored in corresponding train (and test) files.
"""
import os
import subprocess

data_path_lr = "vw/lr/data"    # Linear Regression data path
model_path_lr = "vw/lr/data"   # Linear Regression model/output path

data_path_cb = "vw/cb/data"    # Contextual Bandit data path


def create_training_data_lr():
    f = open("{path}/train.txt".format(path=data_path_lr), "w")
    f.write("0 | price:.23 sqft:.25 age:.05 2006\n")
    f.write("1 | price:.18 sqft:.15 age:.35 1976\n")
    f.write("0 | price:.53 sqft:.32 age:.87 1924\n")
    f.close()


def create_test_data_lr():
    f = open("{path}/test.txt".format(path=data_path_lr), "w")
    f.write("| price:.46 sqft:.4 age:.10 1924\n")
    f.close()


def train_model_lr():
    subprocess.call(
        "vw -d {data_path}/train.txt -f {model_path}/model.vw".format(
            data_path=data_path_lr,
            model_path=model_path_lr),
        shell=True)


def test_model_lr():
    subprocess.call(
        "vw -d {data_path}/test.txt -i {model_path}/model.vw -p {model_path}/predictions.txt".format(
            data_path=data_path_lr,
            model_path=model_path_lr),
        shell=True)


def create_training_data_cb():
    f = open("{path}/train.dat".format(path=data_path_cb), "w")
    f.write("1:2:0.4 | a c\n")
    f.write("3:0.5:0.2 | b d\n")
    f.write("4:1.2:0.5 | a b c\n")
    f.write("2:1:0.3 | b c\n")
    f.write("3:1.5:0.7 | a d\n")
    f.close()


def train_model_cb():
    subprocess.call(
        "vw -d {path}/train.dat --cb_explore 4 --epsilon 0.2".format(path=data_path_cb),
        shell=True)


# Training and testing models
if __name__ == '__main__':

    print("Starting training and testing using VW command line.")

    # Linear Regression
    os.makedirs(data_path_lr, exist_ok=True)
    os.makedirs(model_path_lr, exist_ok=True)

    create_training_data_lr()
    create_test_data_lr()
    train_model_lr()
    test_model_lr()

    # Contextual Bandits
    os.makedirs(data_path_cb, exist_ok=True)

    create_training_data_cb()
    train_model_cb()

    print("Training and testing completed!")
