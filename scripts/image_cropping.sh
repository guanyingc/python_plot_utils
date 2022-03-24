#python img_tools/image_cropper.py --in_dir examples/image_cropper_example/ --key '*.jpg' \
#    --save_dir ROI --save_ext .jpg \
#    --boxes 118 60 193 150 --boxes 371 452 431 521 --colors r g

python img_tools/image_cropper.py --in_dir examples/image_cropper_example/ --key '*.jpg' \
    --save_dir ROI_arrow --save_ext .jpg \
    --boxes 118 60 193 150 --boxes 371 452 431 521 --colors r g \
    --arrows 86 138 99 154 --arrows 502 412 488 393 --arrow_color r g
