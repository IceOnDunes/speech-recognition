""" Classe Data generator pour génerer les données par batch durant l'apprentissage "on the fly" 
    code de classe inspiré de : https://stanford.edu/~shervine/blog/keras-how-to-generate-data-on-the-fly
    Ajout de la partie pre-traitement (normalisation, calcul de spectrogramme, padding ...) 
"""


import numpy as np
import tensorflow as tf
import string
import librosa
from scipy.io import wavfile


class DataGenerator(tf.keras.utils.Sequence):

    'Generates data for Keras'
    def __init__(self, list_IDs,shuffle=False, batch_size=32, window_len=128,nfft=256,hop_len=127):
        'Initialization'
        self.list_IDs = list_IDs
        self.hop_len = hop_len
        self.batch_size = batch_size
        self.nfft= nfft
        self.window_len = window_len
        self.shuffle = shuffle
        self.on_epoch_end()
        self.char_dict =  { ' ': 0,
                            'a': 1,
                            'b' : 2,
                            'c' : 3,
                            'd' : 4,
                            'e' : 5,
                            'f' : 6,
                            'g' : 7,
                            'h' : 8,
                            'i' : 9,
                            'j' : 10,
                            'k' : 11,
                            'l' : 12,
                            'm' : 13,
                            'n' : 14,
                            'o' : 15,
                            'p' : 16,
                            'q' : 17,
                            'r' : 18,
                            's' : 19,
                            't' : 20,
                            'u' : 21,
                            'v' : 22,
                            'w' : 23,
                            'x' : 24,
                            'y' : 25,
                            'z' : 26
                            }
                          
    def __len__(self):
        'Denotes the number of batches per epoch'
        return int(np.floor(len(self.list_IDs) / self.batch_size))

    def __getitem__(self, index):
        'Generate one batch of data'
        # Generate indexes of the batch
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]

        # Find list of IDs
        list_IDs_temp = [self.list_IDs[k] for k in indexes]

        # Generate data
        X, y = self.__data_generation(list_IDs_temp)

        return X, y

    def on_epoch_end(self):
        'Updates indexes after each epoch'
        self.indexes = np.arange(len(self.list_IDs))
        if self.shuffle == True:
            np.random.shuffle(self.indexes)

    def get_data (self,data_IDs):
      """renvoie le son ainsi que son text associé normalisé """

      son = []
      text = []

      "récuperer les characters de ponctuations"
      ponctuation_char = set(string.punctuation)

      for d in data_IDs:
          fe, audio = wavfile.read(d)
          moyenne = audio.mean()
          std = audio.std()
          audio = (audio-moyenne) / std
          son.append(audio)

          text_path = d[:-8] + '.TXT'  # conversion chemin audio vers chemin text correspondant
          txt = open( text_path, 'r')
          ligne = txt.readline()


          # normaliser les texts
          result = ''.join([i for i in ligne if (not i.isdigit() and i not in ponctuation_char )]).lstrip().lower().replace("\n", '')
          text.append(result)
      return son, text


    def get_padded_mel_spectro(self,audio, maxlen):
        mel_spectro =np.log(np.absolute(librosa.stft(audio.astype(float),  n_fft= self.nfft,hop_length=self.hop_len, win_length=self.window_len)))
        x_len = mel_spectro.shape[1]

        padded_spectro = tf.keras.preprocessing.sequence.pad_sequences(mel_spectro,maxlen=maxlen, dtype='float', padding='post', truncating='post',value=float(255))
        return padded_spectro, x_len

    def extract_features(self, x_data_init):
      #extract longest spectrogram length
        mel_spectrogram = np.log(np.absolute(librosa.stft(max(x_data_init, key=len).astype(float),n_fft= self.nfft,hop_length=self.hop_len, win_length=self.window_len)))
        x_max_length = mel_spectrogram.shape[1]
        # x_max_length = 640
        x_data = []
        x_data_len = []

        for i in range(len(x_data_init)):

            padded_spectro, x_len = self.get_padded_mel_spectro(x_data_init[i], maxlen=x_max_length)

            x_data.append(padded_spectro.T)
            x_data_len.append(x_len) 

        #convert to array
        data_input = np.array(x_data)
        input_length = np.array(x_data_len)

        return data_input,input_length

#changer les noms
    def encode_text(self, y_data_init):

        y_max_length = len(max(y_data_init, key=len))
        y_data = []
        y_data_len = []

        for i in range(len(y_data_init)):
            encoded = []
            for c in y_data_init[i]:
                if c=='':
                  # changer map char et ajouter en haut
                    encoded.append(self.char_dict['<SPACE>'])
                else:
                  encoded.append(self.char_dict[c])

            y_len = len(encoded)


            for j in range(len(encoded), y_max_length):
                    encoded.append(float(255))
            y_data.append(encoded)
            y_data_len.append(y_len)

        # convert to array
        y_data = np.array(y_data)
        label_length = np.array(y_data_len)

        return y_data, label_length


    def __data_generation(self, list_IDs_temp):
       # Generate data
        x_data_init, y_data_init = self.get_data(list_IDs_temp)

        #compute the spec frame of the longest audio
        x_data, input_length = self.extract_features(x_data_init)
        y_data, label_length = self.encode_text(y_data_init)

        inputs = [x_data, y_data, input_length, label_length]
        outputs = np.zeros([self.batch_size])
        return inputs,outputs