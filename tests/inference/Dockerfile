# The FROM statement will be injected at runtime based on the
ARG BASE_IMAGE

FROM $BASE_IMAGE

COPY env.yml /var/azureml-app/

RUN conda install conda==4.12.0 python=3.8 && conda env update --name=base -f /var/azureml-app/env.yml \
		   && conda clean -aqy \
		   && rm -rf /root/.cache/pip


ENV VIRTUAL_ENV=py38

RUN python3.8 -m venv $VIRTUAL_ENV

# pip install of external libraries are for the test_post_with_model test. Other tests don't need this
RUN . $VIRTUAL_ENV/bin/activate\
			&& $VIRTUAL_ENV/bin/pip install --upgrade pip\
			&& pip install azureml-defaults scikit-learn==0.24.2 scipy==1.7.1 joblib==1.0.1

CMD . $VIRTUAL_ENV/bin/activate && runsvdir /var/runit