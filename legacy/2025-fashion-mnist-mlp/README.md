# Fashion Images Classification with Custom Dataset

colab link : https://colab.research.google.com/drive/1nggGzydIOPavVow4b_PZy0oyHd9J3IcQ?usp=sharing

## Dataset

As instructed in MTE evaluation a custom dataset was created with 500 more images

In this project, we utilized the Fashion MNIST dataset as the primary source for training an image classification model. To enhance the model's performance and ability to recognize specific clothing items (shirts, in this case), we created a custom dataset. This dataset consists of 500 additional images of shirts, collected and pre-processed to align with the Fashion MNIST format.

## Preprocessing

The custom shirt images underwent the following preprocessing steps:

1.  **Resizing:** All images were resized to 28x28 pixels, matching the dimensions of the Fashion MNIST images.
2.  **Grayscale Conversion:** Images were converted to grayscale to ensure consistency with the Fashion MNIST dataset, which also uses grayscale images.
3.  **Normalization:** Pixel values of both the original Fashion MNIST and custom dataset images were normalized by dividing by 255. This scales the pixel values to a range of 0 to 1, which can improve model training.

## Model Building

We employed a sequential model using TensorFlow's Keras API. The model architecture is as follows:

1.  **Input Layer:** A Flatten layer to convert the 2D images (28x28 pixels) into a 1D vector.
2.  **Hidden Layers:** Multiple Dense layers with ReLU activation functions for feature extraction.
3.  **Output Layer:** A Dense layer with softmax activation to predict the probability of each of the 10 clothing classes (T-shirt/top, Trouser, Pullover, Dress, Coat, Sandal, Shirt, Sneaker, Bag, Ankle boot).

## Training

The model was trained using the combined dataset (original Fashion MNIST + custom shirt images). We used the Adam optimizer and SparseCategoricalCrossentropy loss function. To prevent overfitting, we implemented early stopping, which monitors the validation loss and stops training if it doesn't improve for a certain number of epochs.

## Evaluation

We evaluated the model's performance on a held-out test set using metrics like accuracy and a confusion matrix. The confusion matrix provides a detailed visualization of the model's predictions, highlighting which classes are easily confused with others.

## Predictions

The trained model can be used to predict the class labels of new, unseen images. By providing an input image, the model outputs the predicted probabilities for each clothing class, allowing us to determine the most likely class label.

## Further Improvements

While the model achieved reasonable accuracy, several potential improvements could be explored:

*   **Data Augmentation:** Applying data augmentation techniques (rotation, scaling, flipping) to the training data could increase the model's robustness and generalization ability.
*   **Hyperparameter Tuning:** Experimenting with different hyperparameters (number of layers, units, activation functions, optimizer settings) could further enhance performance.
*   **Regularization:** Techniques like dropout or L1/L2 regularization could help prevent overfitting.
*   **Transfer Learning:** Leveraging pre-trained models could significantly reduce training time and potentially improve accuracy.