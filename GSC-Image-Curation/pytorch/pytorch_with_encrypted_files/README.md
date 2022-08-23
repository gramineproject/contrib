## You can use the below command to create encrypted files

For simplicity, we have already created the encrypted files into the encrypted directory.

Note: `alexnet-pretrained.pt` file is a more than 200 MB file, hence we are not providing this file
as part of this package. User is advised to follow `pytorch_with_plain_text_files/README.md` to
download this file. Afterwards, user can use the below command to created encrypted version of
`alexnet-pretrained.pt` file.

```sh

$ gramine-sgx-pf-crypt encrypt -w wrap-key -i ../pytorch_with_plain_text_files/plaintext/input.jpg -o input.jpg
$ gramine-sgx-pf-crypt encrypt -w wrap-key -i ../pytorch_with_plain_text_files/plaintext/classes.txt -o classes.txt
$ gramine-sgx-pf-crypt encrypt -w wrap-key -i ../pytorch_with_plain_text_files/plaintext/alexnet-pretrained.pt -o alexnet-pretrained.pt
mv input.jpg classes.txt alexnet-pretrained.pt ./encrypted
```

## Building pytorch plain image

`docker build -t <pytorch-image-with-encrypted-files> .`

once the image is created , please refer `GSC-Image-Curation/README.md` to create the
<gsc-pytorch-image-with-encrypted-files> image

Note: Since, this image contains encrypted files, please provide the below string when prompted for
encrypted files option `classes.txt:input.jpg:alexnet-pretrained.pt:app/result.txt` during gsc image
creation.
