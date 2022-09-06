
import keras
from keras import layers, models
import numpy as np
import os
from keras.preprocessing import image
import gzip
from matplotlib import pyplot as plt
from keras.datasets import mnist, cifar10
from keras import backend as K
K.set_image_dim_ordering('tf')
from sklearn.utils import shuffle
import cv2


#train_data = extract_data('train-images-idx3-ubyte.gz', 60000)
#test_data = extract_data('t10k-images-idx3-ubyte.gz', 10000)
#train_labels = extract_labels('train-labels-idx1-ubyte.gz',60000)
#test_labels = extract_labels('t10k-labels-idx1-ubyte.gz',10000)

(train_data, train_labels), (_, _) =mnist.load_data()
train_data = train_data.reshape(-1, 28,28,1).astype('float32')

curr_img = np.reshape(train_data[10], (28,28))
#plt.imshow(cv2.cvtColor(curr_img, cv2.COLOR_BGR2RGB))
plt.imshow(curr_img, cmap = 'gray')
plt.show()

train_data = (train_data - 127.5)/127.5

# Display the first image in training data

latent_dim = 100
channels =1
height =28
width = 28

##generator network
generator_input = keras.Input(shape=(latent_dim, ))

x = layers.Dense(128 * 7 * 7)(generator_input)
x = layers.BatchNormalization()(x)
x = layers.LeakyReLU()(x)

x = layers.Reshape((7,7,128))(x)

x = layers.Conv2DTranspose(128, 5, strides=1, padding='same')(x)
x = layers.BatchNormalization()(x)
x = layers.LeakyReLU()(x)

x = layers.Conv2DTranspose(64, 5, strides=2, padding='same')(x) # 14*14*256 upsampling
x = layers.BatchNormalization()(x)
x = layers.LeakyReLU()(x)

x = layers.Conv2DTranspose(channels, 5, strides=2, padding='same', activation='tanh')(x) # 28*28*channels upsampling


generator = models.Model(generator_input, x)
#generator.summary()

#descriminator network
descriminator_input = layers.Input(shape=(height, width, channels))

x = layers.Conv2D(64, 5)(descriminator_input)
#x = layers.BatchNormalization()(x)
x = layers.LeakyReLU()(x)
x = layers.Dropout(0.25)(x)

x = layers.Conv2D(128, 5, strides=2)(x)
#x = layers.BatchNormalization()(x)
x = layers.LeakyReLU()(x)
x = layers.Dropout(0.25)(x)


#x = layers.Conv2D(128, 4, strides=2)(x)
#x = layers.BatchNormalization(momentum=0.8)(x)
#x = layers.LeakyReLU()(x)
#x = layers.Dropout(0.25)(x)

x = layers.Flatten()(x)
x = layers.Dense(128)(x)
x = layers.LeakyReLU()(x)
x = layers.Dropout(0.3)(x)

x = layers.Dense(1, activation='sigmoid')(x)
descriminator = models.Model(descriminator_input, x)
#descriminator.summary()

#descriminator_optimizer = keras.optimizers.Adam(lr=0.0004,clipvalue=1.0, decay=1e-8)
descriminator_optimizer = keras.optimizers.Adam(lr=0.0001)

descriminator.compile(optimizer=descriminator_optimizer, loss='binary_crossentropy')

descriminator.trainable = False

#gan
gan_input = layers.Input(shape=(latent_dim, ))
gan_output = descriminator(generator(gan_input))
gan = models.Model(gan_input, gan_output)

#gan_optimizer = keras.optimizers.Adam(lr=0.0004,clipvalue=1.0, decay=1e-8)
gan_optimizer = keras.optimizers.Adam(lr=0.0004)#,clipvalue=1.0, decay=1e-8)
gan.compile(optimizer=gan_optimizer, loss='binary_crossentropy')


from sklearn.model_selection import train_test_split

train_X, _ , _ , _ = train_test_split(train_data, train_labels, test_size=0.0, random_state=0)

X_train  = train_X


iterations = 2000
batch_size = 128
#save_dir = "./gan_generated_1"
start = 0

for step in range(iterations):
    random_latent_vectors = np.random.normal(size=(batch_size, latent_dim)) #sample random points
    generated_images = generator.predict(random_latent_vectors) #output of the generator (decoded fake images)
    
    stop = start + batch_size
    real_images = X_train[start:stop]
    combined_images = np.concatenate([generated_images, real_images])#combine fake and real images
    
    labels = np.concatenate([np.zeros((batch_size, 1)), np.ones((batch_size, 1))])
    combined_images, labels = shuffle(combined_images,labels )
    
    #labels += 0.05*np.random.random(size=labels.shape) #add noise to the labels
    
    d_loss = descriminator.train_on_batch(combined_images, labels) #train the descriminator
    
    random_latent_vectors = np.random.normal(0,1,size = (batch_size, latent_dim))#sample random vectors
    misleading_targets = np.ones((batch_size, 1)) #labels that lie that they are real images
    
    a_loss = gan.train_on_batch(random_latent_vectors, misleading_targets) #train generator model via gan
    
    start += batch_size
    if start > len(X_train)-batch_size:
        start = 0
    
    if step %100 ==0:
        gan.save_weights('gan.h5')
        
        print("descriminator loss ",step," : ", d_loss)
        print("adverserial loss : ",step," : ", a_loss)
        
        #if step %100 == 0:
          #plt.imshow(generated_images[0].reshape(28,28), cmap='gray')
          #plt.show()
        #img = image.array_to_img(generated_images[0] * 255., scale=False)
        #img.save(os.path.join(save_dir, "generated_"+str(step)+'.png'))
        #img = image.array_to_img(real_images[0] * 255., scale=False)
        #img.save(os.path.join(save_dir, "real_"+str(step)+'.png'))

#generator.save('ganfinal.h5')

import matplotlib.pyplot as plt
new_random_latent_vectors = np.random.normal(size=(10, latent_dim)) #sample random points
#print(new_random_latent_vectors)
#print(new_random_latent_vectors.shape)
new_generated_images = generator.predict(new_random_latent_vectors) #output of the generator (decoded fake images)

print(new_generated_images[0].shape)
#print(np.max(new_generated_images[0]*127.5 + 127.5))

for i in range(new_generated_images.shape[0]):
  #img = image.array_to_img(new_generated_images[i].reshape((28,28,1))*127.5 + 127.5, scale=False)
  
  plt.imshow(new_generated_images[i].reshape((28,28))*127.5 + 127.5, cmap='gray')
  plt.show()

