# system library
import numpy as np
import json

# user-library
import ClassficationBase


# third-party library
from sklearn import neighbors
from sklearn import linear_model
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import RandomForestClassifier

import lasagne
from lasagne import layers
from lasagne.updates import nesterov_momentum
from nolearn.lasagne import NeuralNet
from sklearn.linear_model import Perceptron


class ClassificationUniformBlending(ClassficationBase.ClassificationBase):
    def __init__(self, isTrain, isOutlierRemoval=0):
        super(ClassificationUniformBlending, self).__init__(isTrain, isOutlierRemoval)
        # data preprocessing
        self.dataPreprocessing()

        # create logistic regression object
        self.logreg = linear_model.LogisticRegression(tol=1e-6, penalty='l1', C=0.0010985411419875584)

        # create adaboost object
        self.dt_stump = DecisionTreeClassifier(max_depth=10)
        self.ada = AdaBoostClassifier(
            base_estimator=self.dt_stump,
            learning_rate=1,
            n_estimators=5,
            algorithm="SAMME.R")

        # create knn object
        self.knn = neighbors.KNeighborsClassifier(2, weights='uniform')

        # create decision tree object
        self.decisiontree = DecisionTreeClassifier(max_depth=45, max_features='log2')

        # create neural network object
        self.net1 = NeuralNet(
                        layers=[  # three layers: one hidden layer
                            ('input', layers.InputLayer),
                            ('hidden', layers.DenseLayer),
                            #('hidden2', layers.DenseLayer),
                            ('output', layers.DenseLayer),
                            ],
                        # layer parameters:
                        input_shape=(None, 12),  # inut dimension is 12
                        hidden_num_units=6,  # number of units in hidden layer
                        #hidden2_num_units=3,  # number of units in hidden layer
                        output_nonlinearity=lasagne.nonlinearities.sigmoid,  # output layer uses sigmoid function
                        output_num_units=1,  # output dimension is 1

                        # optimization method:
                        update=nesterov_momentum,
                        update_learning_rate=0.002,
                        update_momentum=0.9,

                        regression=True,  # flag to indicate we're dealing with regression problem
                        max_epochs=25,  # we want to train this many epochs
                        verbose=0,
                        )

        # create PLA object
        self.pla = Perceptron()

        # create random forest object
        self.rf = RandomForestClassifier(max_features='log2', n_estimators=20, max_depth=30)




    def dataPreprocessing(self):
        # deal with unbalanced data
        self.dealingUnbalancedData()

        # Standardization
        #self.Standardization()



    def training(self):
        # train the models
        self.logreg.fit(self.X_train, self.y_train.ravel())
        self.ada.fit(self.X_train, self.y_train.reshape((self.y_train.shape[0], )))
        self.knn.fit(self.X_train, self.y_train.ravel())
        self.decisiontree.fit(self.X_train, self.y_train)
        self.net1.fit(self.X_train, self.y_train)
        self.pla.fit(self.X_train, self.y_train.ravel())
        self.rf.fit(self.X_train, self.y_train.ravel())

    def predict(self):
        # predict the test data
        y_pred1 = self.logreg.predict(self.X_test)
        y_pred1 = y_pred1.reshape((y_pred1.shape[0], 1))

        y_pred2 = self.ada.predict(self.X_test)
        y_pred2 = y_pred2.reshape((y_pred2.shape[0], 1))

        y_pred3 = self.knn.predict(self.X_test)
        y_pred3 = y_pred3.reshape((y_pred3.shape[0], 1))

        y_pred4 = self.decisiontree.predict(self.X_test)
        y_pred4 = y_pred4.reshape((y_pred4.shape[0], 1))

        # predict neural network
                # predict the test data
        y_pred_train = self.net1.predict(self.X_train)
        y_pred5 = self.net1.predict(self.X_test)
        # 1 for buy, 0 for wait
        median = np.median(y_pred_train)
        mean = np.mean(y_pred_train)
        y_pred5[y_pred5>=median] = 1  # change this threshold
        y_pred5[y_pred5<median] = 0
        y_pred5 = y_pred5.reshape((y_pred5.shape[0], 1))

        y_pred6 = self.pla.predict(self.X_test)
        y_pred6 = y_pred6.reshape((y_pred6.shape[0], 1))

        y_pred7 = self.rf.predict(self.X_test)
        y_pred7 = y_pred7.reshape((y_pred7.shape[0], 1))

        # predict the blending output
        self.y_pred = (y_pred1+y_pred2+y_pred3+y_pred4+y_pred5 + y_pred7)/6
        self.y_pred[self.y_pred >= 0.5] = 1
        self.y_pred[self.y_pred < 0.5] = 0

        # print the error rate
        e1 = 1 - np.sum(self.y_test == y_pred1) * 1.0 / y_pred1.shape[0]
        e2 = 1 - np.sum(self.y_test == y_pred2) * 1.0 / y_pred2.shape[0]
        e3 = 1 - np.sum(self.y_test == y_pred3) * 1.0 / y_pred3.shape[0]
        e4 = 1 - np.sum(self.y_test == y_pred4) * 1.0 / y_pred4.shape[0]
        e5 = 1 - np.sum(self.y_test == y_pred5) * 1.0 / y_pred5.shape[0]
        e6 = 1 - np.sum(self.y_test == y_pred6) * 1.0 / y_pred6.shape[0]
        e7 = 1 - np.sum(self.y_test == y_pred7) * 1.0 / y_pred7.shape[0]
        err = 1 - np.sum(self.y_test == self.y_pred) * 1.0 / self.y_pred.shape[0]
        print "Log Reg err = {}".format(e1)
        print "Ada err = {}".format(e2)
        print "KNN err = {}".format(e3)
        print "DT eRR = {}".format(e4)
        print "NN err = {}".format(e5)
        print "PLA err = {}".format(e6)
        print "RandomForest err = {}".format(e7)
        print "Uniform error = {}".format(err)


