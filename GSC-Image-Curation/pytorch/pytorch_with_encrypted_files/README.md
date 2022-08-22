## You can use the below command to create encrypted files

For simplicity, we have already created the encrypted files into the encrypted directory.

Note: alexnet-pretrained.pt file is a more than 200 MB file, hence we are not providing this file as part of this package.
      User is advised to follow `pytorch_with_plain_text_files/README.md` to download this file. Afterwards, user can use the below command to created encrypted version of alexnet-pretrained.pt file.

```sh

$ gramine-sgx-pf-crypt encrypt -w wrap-key -i ../pytorch_with_plain_text_files/plaintext/input.jpg -o input.jpg
$ gramine-sgx-pf-crypt encrypt -w wrap-key -i ../pytorch_with_plain_text_files/plaintext/classes.txt -o classes.txt
$ gramine-sgx-pf-crypt encrypt -w wrap-key -i ../pytorch_with_plain_text_files/plaintext/alexnet-pretrained.pt -o alexnet-pretrained.pt
mv input.jpg classes.txt alexnet-pretrained.pt ./encrypted
```

## Building pytorch plain image

`docker build -t <pytorch-image-with-encrypted-files> .`
Once the image is created , please use `GSC-Image-Curation/curation_script.sh` to create the <pytorch-image-with-encrypted-files> image

Note: Since, this image contains encrypted files, please select "y", when prompted for encrypted files option while using `GSC-Image-Curation/curation_script.sh`. Also, please provide encrytped files input as follows: `classes.txt:input.jpg:alexnet-pretrained.pt:app/result.txt`
