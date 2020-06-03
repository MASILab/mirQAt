import typer

import pandas as pd
import pydicom
from pathlib import Path

app = typer.Typer(help="mirQAT: Medical Imaging Research QA Toolkit")

@app.command()
def dcm_instance(dcm_root):
    """
    Check instance numbers in a DICOM folder. Does the instance number match the number of DICOMs in each session?
    Returns (<num1>, <num2>, <num3>)

    Valid: if <num1> == <num2> & <num3> == 0 (<num3> is the diff b/w num1 and num2).
    Invalid: if <num1> != <num2>, i.e. <num3> != 0.
    """
    if Path(dcm_root).exists() == False:
        print("This folder does not exist. Please input an existing folder path.")
    dcm_list = list(Path(dcm_root).glob("**/*.dcm"))
    # dcm_list = glob(os.path.join(dcm_root, "*.dcm"))
    if len(dcm_list) == 0:
        print(
            "We were unable to find DICOM files in this root directory. Please review path and try again."
        )
    #slicePos = []
    instanceN = []
    for i in range(len(dcm_list)):
        ds = pydicom.dcmread(str(dcm_list[i]))
        # slicePos.append(ds.SliceLocation)
        instanceN.append(ds[0x20, 0x13].value)
    #print("max and min of instanceN ", max(instanceN), min(instanceN))
    #typer.secho(f"Max and Min of instanceN is {max(instanceN)} and {min(instanceN)}", fg=typer.colors.GREEN)
    return (
        len(instanceN),
        max(instanceN) - min(instanceN) + 1,
        max(instanceN) - min(instanceN) + 1 - len(instanceN),
    )

@app.command()
def instanceN_fold(fold_root, save_csv_path="instance_num_check.csv"):
    """
    Generates a CSV file comparing instance number, no. of DICOM images.

    Arguments:
        - Root folder
        - Location and name to store CSV output
    Output csv file:
        - instance number using header info
        - if only single folder
        - number of DICOM images for a particular session
        - difference b/w # of DICOM images and Instance number
            - Valid values are those <= 0 (?)
    """
    subj_list = [x.stem for x in Path(fold_root).iterdir() if x.is_dir()]
    sess, single_folder, instanceN, dicomN, diff = [], [], [], [], []
    with typer.progressbar(range(0, len(subj_list)), label="Subjects") as subj_prog:
        for i in subj_prog:
            subj_path = Path(fold_root) / subj_list[i]
            sess_list = [x.stem for x in Path(subj_path).iterdir() if x.is_dir()]
            for j in range(len(sess_list)):
                sess.append(sess_list[j])
                # print("(i, j): ", i, j, sess_list[j])
                sess_path = subj_path / sess_list[j]
                instance_list = [x.stem for x in Path(sess_path).iterdir() if x.is_dir()]
                if len(instance_list) == 1:
                    single_folder.append(1)
                else:
                    single_folder.append(0)
                size_list = []
                for k in range(len(instance_list)):
                    p = sess_path / instance_list[k]
                    size_list.append(len(list(p.rglob("*.dcm"))))
                    # print(sess_path / instance_list[k])
                    # if (sess_path / instance_list[k] / "secondary").exists() and not (sess_path / instance_list[k] / "DICOM").exists():    # Unnecessary if not dealing with DICOM subdir
                    #    (sess_path / instance_list[k] / "secondary").rename(sess_path / instance_list[k] / "DICOM")
                    # size = len(os.listdir(sess_path + "/" + instance_list[k] + "/DICOM")) # There is no DICOM subdirectory, so this throws an error
                    # size = len([x for x in  if x.is_dir()])
                    # size_list.append(size)
                max_index = size_list.index(max(size_list))
                # break

                # Renames the dir with the greatest # of dcm image files
                if 'new_max' in [p.stem for p in sess_path.iterdir()]:
                    typer.echo(f"A folder is already called 'new_max'. You may have run this command before. Please review for discrepancies.\n", err=True)
                else:
                    (sess_path / instance_list[max_index]).rename(sess_path / "new_max")
                try:
                    # inst_n, dicom_n, same = dcm_instance(sess_path + "/new_max/DICOM") # Again, there is no DICOM subdirectory, so this throws an error
                    inst_n, dicom_n, same = dcm_instance(sess_path / "new_max")
                    instanceN.append(inst_n)
                    dicomN.append(dicom_n)
                    diff.append(same)
                except:
                    instanceN.append("")
                    dicomN.append("")
                    diff.append("")
                    print("dicom error")
    data = pd.DataFrame()
    data["sess"] = sess
    data["single_folder"] = single_folder
    data["instanceN"] = instanceN
    data["dicomN"] = dicomN
    data["dicomN-instanceN"] = diff
    data.to_csv(save_csv_path, index=False)
    typer.secho(f"Instance number checking complete! Please review output in file: {str(save_csv_path)}.", fg=typer.colors.GREEN)



@app.command()
def dcm_slicedistance(dcm_root):
    """
    Calculate slice distance given a directory or subdirectories with DICOM images.
    """
    if Path(dcm_root).exists() == False:
        print("This folder does not exist. Please input an existing folder path.")
    dcm_list = list(Path(dcm_root).glob("**/*.dcm"))
    # dcm_list = os.listdir(dcm_root)
    # dcm_list = glob(os.path.join(dcm_root, "*.dcm"))
    ds_list = []
    # skipped_accession = []
    for i in range(len(dcm_list)):
        # ds = pydicom.dcmread(dcm_list[i])
        ds = pydicom.dcmread(str(dcm_list[i]))
        if hasattr(ds, "SliceLocation"):  # some images do not have 'SliceLocation'
            ds_list.append(ds.SliceLocation)
    #       else:
    #           skipped_accession.append(ds.AccessionNumber)

    #   print(f'The following accession numbers have missing "SliceLocation": {Counter(skipped_accession)}.')
    ds_sort = sorted(ds_list, reverse=True)
    res = 1
    for i in range(0, len(ds_sort) - 2):
        #print((ds_sort[i] - ds_sort[i + 1]), (ds_sort[i + 1] - ds_sort[i + 2]))
        if not abs(
            (ds_sort[i] - ds_sort[i + 1]) - (ds_sort[i + 1] - ds_sort[i + 2])
        ) < (ds_sort[0] - ds_sort[1]):
            res = 0
    return res

@app.command()
def sliceDis_fold(fold_root, save_csv_path='slice_dist_check.csv'):
    """
    Generates a csv file with DICOM slice distance information.

    Arguments:
        - Root folder
        - Location and name to store CSV output
    Output csv file:
        - Instance number
        - If only one instance: single folder = 1 or 0 otherwise
        - distance_check: Output of `dcm_slicedistance` function calculated for each session
    """
    subj_list = [x.stem for x in Path(fold_root).iterdir() if x.is_dir()]
    sess, single_folder, diff = [], [], []
    with typer.progressbar(range(0, len(subj_list)), label="Subjects") as subj_prog:
        for i in subj_prog:
            # if i > 3: break
            subj_path = Path(fold_root) / subj_list[i]
            sess_list = [x.stem for x in Path(subj_path).iterdir() if x.is_dir()]
            for j in range(len(sess_list)):
                sess.append(sess_list[j])
                #print("(i, j): ", i, j, sess_list[j])
                sess_path = subj_path / sess_list[j]
                instance_list = [x.stem for x in Path(sess_path).iterdir() if x.is_dir()]
                if len(instance_list) == 1:
                    single_folder.append(1)
                else:
                    single_folder.append(0)
                try:
                    #same = dcm_slicedistance(sess_path + "/new_max/DICOM") # the DICOM files are under `new_max` and not `new_max/DICOM`
                    same = dcm_slicedistance(sess_path / "new_max")
                    diff.append(same)
                except:
                    try:
                        same = dcm_slicedistance(sess_path / "file0/DICOM")
                        diff.append(same)
                    except:
                        diff.append("")

                        print("dicom error")
    data = pd.DataFrame()
    data["sess"] = sess
    data["single_folder"] = single_folder
    data["distance_check"] = diff
    data.to_csv(save_csv_path, index=False)
    typer.secho(f"Slice distance check complete! Please review output in file: {str(save_csv_path)}.", fg=typer.colors.GREEN)

@app.command()
def filter_few_slices(csv_path='instance_num_check.csv'):
    """
    Filter to exclude sessions with few slices (less than 20) but that pass instance number check (dicomN - instanceN > 0).
    
    TODO: should we allow the thresholds to be user-definable parameters.
    """
    df = pd.read_csv(csv_path)
    auto_QA_result = []
    for i, item in df.iterrows():
        if item["dicomN-instanceN"] > 0 or item["instanceN"] < 20:
            auto_QA_result.append("bad")
        else:
            auto_QA_result.append("good")
    df["auto"] = auto_QA_result
    df.to_csv(csv_path, index=False)
    typer.secho('Filtering completed. Review instance number check CSV file for updated output.', fg=typer.colors.GREEN)
