# Transimage

An image translator that can use 3 translators (Google, Bing and DeepL) and two OCR (Tesseract and EasyOCR). 
Text editing is also possible but only in the original language of the image.

**At the moment the Google translator does not work because of this [issue](https://github.com/ssut/py-googletrans/issues/234).**

I wrote this [package](https://github.com/A2va/ImageTranslator) for translating and detecting text on images


![Interface](images/transimage.PNG)

## Usage

1. Open Image
2. Select source and destination language then translator and OCR
3. Click on "Run processing"

### Edition

*  Ctrl+Scroll zoom in and out
* Shift+Ctrl+Scroll move left and right
* Scroll move up and down
* Edit text with a double click on it

4. When your finished your edition you can save the image

## Roadmap

If I have time I will implement this

* Custom font
* Text color and detecting 
* Inpainting and not white rectangle

## Development

```
git clone --recurse-submodules https://github.com/A2va/Transimage.git
pip install -r requirements.txt
pip install torch===1.7.0 torchvision===0.8.1 torchaudio===0.7.0 -f https://download.pytorch.org/whl/torch_stable.html
```
### Build

```
python setup.py build
```


