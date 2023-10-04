# This script loads a dataset of which the last column is supposed to be the class and logs the accuracy
install.packages("caret", repos = "http://cran.us.r-project.org")
install.packages("e1071", repos = "http://cran.us.r-project.org")

library("azuremlsdk")
library("caret")

all_data <- read.csv("iris.csv")

all_data$Species <- as.numeric(all_data$Species == "virginica")
classes <- all_data[, ncol(all_data)]
in_train <- createDataPartition(y = classes, p = .8, list = FALSE)
train_data <- all_data[in_train, ]
test_data <- all_data[-in_train, ]

model <- glm(Species ~ ., family = binomial(link = 'logit'), data = train_data)

predictions <- predict(model, test_data, type = 'response')

conf_matrix <- confusionMatrix(table(as.numeric(predictions > 0.5), test_data$Species), positive = '1')
accuracy <- conf_matrix$overall["Accuracy"]

current_run <- get_current_run()
log_metric_to_run("accuracy", accuracy, current_run)
