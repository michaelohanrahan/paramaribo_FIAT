import os 
import shutil

# --- Functions
def move_the_fou(path, nc_dir):
    if path.endswith('_fou.nc'):
        source = path
        for l, r in zip(list, runs):
            if l in path.split("\\"):
                # print(l,r)
                break
        destination = os.path.join(nc_dir, f"{r}_fou.nc")
        shutil.copy2(source, destination)
    else:
        print(f"not valid: {path}")

def find_the_fou(path):
    fou_first = os.path.join(path, "dflowfm")

    if not os.path.exists(fou_first):
        try:
            new_path = os.path.join(path, "DFLOWFM_fou.nc")
            return new_path
        except:
            print(f"no output directory nor output found in {path}")
    
    else:
        new_path = os.path.join(fou_first, "output", "DFLOWFM_fou.nc")
        print(new_path)
        return new_path

fn = snakemake.input.data_folder
proj = snakmake.input.project_folder
fn_joined = os.path.join(proj, "data", "1-external", fn)
list = os.listdir(fn_joined)
runs = [f'Flood_rp_{("p").join(run.split("."))[1:]}' if '.' in run else f'Flood_rp_{run[1:]}' for run in list]

#Find fou files within and copy them to the interim folder 
interim_dir = os.path.join(proj, "data", "2-interim")


if __name__ == "__main__":
    for folder in list:
        path = os.path.join(fn_joined, folder)
        fou = find_the_fou(path)
        dest_dir = os.path.join(interim_dir, fn); os.makedirs(dest_dir, exist_ok=True)
        nc_dir = os.path.join(dest_dir, 'foufiles'); os.makedirs(nc_dir, exist_ok=True)
        move_the_fou(fou, nc_dir)

