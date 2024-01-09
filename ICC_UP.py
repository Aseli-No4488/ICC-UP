import base64, re, os

from pathlib import Path
from PIL import Image
from tkinter import filedialog, messagebox
from sys import exit

def convert_to(source, file_format = 'webp'):
    """Convert image to WebP.

    Args:
        source (pathlib.Path): Path to source image

    Returns:
        pathlib.Path: path to new image
    """
    
    destination = source.with_suffix(f".{file_format}")

    image = Image.open(source)  # Open image
    image.save(destination, format=file_format)  # Convert image to webp
    
    print(f'CONVERTED - {destination}')
    return destination

def change_base64_to_img(data, format:str, path:str):
    l = re.findall(f'data:image\/{format};base64,' + r"[^\",]+\"", data)
    print(f'Find {len(l)} images! - format: {format}')
    
    for i, base64img in enumerate(l):
        ## Convert base64 to binary
        imgdata = base64.b64decode(base64img[19+len(format):-1])
        
        ## Save image
        with open(f'{path}/img/{format}_{i}.{format}', 'wb') as f: f.write(imgdata)
        
        ## Replace base64 in json
        data = data.replace(base64img[:-1], f'img/{i}.{format}')
    
    return data


if __name__ == '__main__':
    print("="*30)
    print("ICC UP V1.0")
    print("="*30)
    
    # Get project.json
    files = filedialog.askopenfilenames(initialdir=os.getcwd(),\
            title = "project.json 파일을 선택하시오.",\
                filetypes = [("Json File","*.json")])
    
    if files == '':
        messagebox.showwarning("", "파일이 선택되지 않았습니다.")
        exit()
    
    main_path = os.path.dirname(files[0])
    print(f"Path - {main_path}")
    
    
    # Read file
    with open(files[0], 'r', encoding='utf8') as f: data = f.read()
    
    ## Make backup file
    with open(f'{main_path}/project.json.backup', 'w', encoding='utf8') as fb: fb.write(data)
    
    
    # Make img folder
    if not os.path.exists(f'{main_path}/img'):
        os.mkdir(f'{main_path}/img')

    # Convert base64 to img
    data = change_base64_to_img(data, 'jpeg', main_path)
    data = change_base64_to_img(data, 'png', main_path)
    data = change_base64_to_img(data, 'webp', main_path)

    # Apply modification to project.json
    with open(f'{main_path}/project.json', 'w', encoding='utf8') as f:
        f.write(data)
    
    
    # Check if you want to convert all images
    while True:
        user_input = input("Do you want to convert all images to webp? (y/n) : ")
        if (user_input == 'y') or (user_input == 'Y'):
            break
        elif (user_input == 'n') or (user_input == 'N'):
            exit()

    ## Convert all images to webp
    file_path = os.path.abspath(main_path)+"/img"
    file_list = [file_path+'\\'+i for i in os.listdir(file_path) if not i.endswith('.webp')]
    file_list = [Path(i) for i in file_list]

    # Pyinstaller cannot use multiprocessing?    
    # with Pool(8) as p:
    #     p.map(convert_to, file_list)
    for file in file_list: convert_to(file)
        
    ## Apply modification (webp)
    with open(f'{main_path}/project.json', 'w', encoding='utf8') as f:
        f.write(
            data
            .replace('.jpeg', '.webp')
            .replace('.png', '.webp')
        )
    
    for file in file_list:
        if ('jpg' in str(file)) or ('jpeg' in str(file)) or ('png' in str(file)):
            os.remove(file)
            print(f'DELETED - {file}')
    
    
    messagebox.showwarning("", "Done!")
    exit()