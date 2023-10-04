import argparse
import os
from azureml.core.experiment import Experiment
from azureml.core.run import Run
from tests.utils import _get_workspace


parser = argparse.ArgumentParser()
parser.add_argument('--aad_sp_password', help='AAD Service principle password to the workspace')
args = parser.parse_args()

if args.aad_sp_password is None:
    print("AAD Service principle password to the workspace is required.")
    exit(1)

workspace = _get_workspace(args.aad_sp_password)


# Test docker file step submits a lot of parallel jobs.
# This step is to cancel all the jobs in case one of the jobs failed.
# cancelling the runs is important as it will free the AmlCompute queue for the next test run
def _cancel_all_runs():
    # Run information file will not be created if the build didn't reach test dockers step.
    # No need to cancel runs if this step didn't happen
    file_name = "/tmp/run_information.txt"
    if os.path.isfile(file_name):
        with open(file_name) as file:
            all_run_information = file.read().splitlines()
            experiment = None
            for run_information in all_run_information:
                if experiment is None:
                    experiment = Experiment(workspace, run_information.split(" ")[0])
                run_id = run_information.split(" ")[1]
                run = Run(experiment=experiment, run_id=run_id)
                # Azure portal has run number so print run number too
                print("Canceling run id={}, number={} in status {}".format(run_id, run.number, run.get_status()))
                if run.get_status() not in ["Completed", "Canceled", "Failed"]:
                    run.cancel()
    else:
        print("No runs were submitted in this build.")


_cancel_all_runs()
