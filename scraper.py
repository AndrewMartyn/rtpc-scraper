from bs4 import BeautifulSoup
import mechanize
import pandas as pd
import numpy as np
import zipfile
from pathlib import Path
import shutil
import os

# scraped information by set
namesBySet = []
pdfNamesBySet = []
downloadsBySet = []
datesBySet = []
teamsBySet = []
sourcesBySet = []

# Problem fields
source_ids = []
names = []
pdf_paths = []
zip_urls = []

# ProblemSet Fields
problem_ids = []
set_ids = []

# History fields (by problem)
history_problem_ids = []
dates = []
team_ids = []

# Source fields (by category)
sourcesByProblem = []
sourcesByCategory = []


br = mechanize.Browser()

def main():
    login("", "")

    addDataFromURL("https://rtpc.ucfprogrammingteam.org/index.php/downloads/category/41-2021-2022")
    addDataFromURL("https://rtpc.ucfprogrammingteam.org/index.php/downloads/category/40-2020-2021")
    addDataFromURL("https://rtpc.ucfprogrammingteam.org/index.php/downloads/category/38-2019-2020")

    cleanseData()

    # patches
    # pdfNamesBySet[31][7] = 'h'
    # pdfNamesBySet[54][4] = 'minesweeper'
    # pdfNamesBySet[54][7] = 'robotchallenge'

    # fixNames()

    # createProblemZips()

    createProblemsDF()
    createSourceDF()
    createHistoryDF()
    createProblemSetDF()
    createSetsDF()
    createTeamDF()

def fixNames():
    fileNames = [entry.replace(" ", "_") for entry in (f"{name}-{names.index(name)+1}" for name in names)]
    alphabet = ['_', '-', '+', '=', '(', ')', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    newNames = [''.join([c for c in str if c.lower() in alphabet]) for str in fileNames]

    for i in range(0, len(fileNames)):
        print(f"working file {fileNames[i]}-({i}/{len(fileNames)})")
        if os.path.exists(fr"zips/{fileNames[i]}.zip"):
            print(f"Renaming {fileNames[i]}.zip to {newNames[i]}.zip")
            os.rename(fr"zips/{fileNames[i]}.zip", fr"zips/{newNames[i]}.zip")
        if os.path.exists(fr"pdfs/{fileNames[i]}.pdf"):
            print(f"Renaming {fileNames[i]}.pdf to {newNames[i]}.pdf")
            os.rename(fr"pdfs/{fileNames[i]}.pdf", fr"pdfs/{newNames[i]}.pdf")

def createProblemZips():
    for i in range(118, len(downloadsBySet)):
        download = downloadsBySet[i]
        zipName = download.split(":")[2]
        print(f"Working on {zipName}-({i}/{len(downloadsBySet)})...")

        br.retrieve(download, zipName+".zip")
        # extract archive to folder
        try:
            with zipfile.ZipFile(zipName+".zip") as archive:
                archive.extractall(zipName)
        except zipfile.BadZipFile:
            print("Bad zip file, skipping")
            os.remove(zipName+".zip")
            continue

        # create a new folder for individual zips
        pdfNames = pdfNamesBySet[i]
        problemNames = namesBySet[i]
        for j in range(0, len(pdfNames)):
            pdfName = pdfNames[j]
            rawProblemName = problemNames[j]
            problemIndex = names.index(rawProblemName)+1
            problemName = rawProblemName.replace(" ", "_")

            name = f"{problemName}-{problemIndex}"
            print(f"Working on problem {problemName}({pdfName})-{problemIndex}...")
            if(os.path.exists(fr"zips/{name}.zip") or os.path.exists(fr"pdfs/{name}.pdf")):
                print(f"problem {problemName} already exists, skipping...")
                continue
            

            try:
                shutil.copytree(fr"{zipName}/samples/{pdfName}", fr"zips/{name}/samples")     
            except:
                pass

            try:
                shutil.copytree(fr"{zipName}/data/{pdfName}", fr"zips/{name}/data")
            except:
                pass
            
            try:
                shutil.copyfile(fr"{zipName}/problems/{pdfName}.pdf", fr"pdfs/{name}.pdf")
            except:
                pass

            shutil.make_archive(fr"zips/{name}", "zip", fr"zips/{name}")
            shutil.rmtree(fr"zips/{name}")

        shutil.rmtree(fr"{zipName}")
        os.remove(fr"{zipName}.zip")
        print(f"Done with {zipName}!\n")


def cleanseData():
    # convert 2d problem array to 1d
    namesWithDupes = []
    for set in namesBySet:
        for name in set:
            namesWithDupes.append(name)

    df = pd.DataFrame(namesWithDupes, columns=['names'])
    df.loc[df['names'].duplicated(), 'names'] = None
    namesWithNone = df['names'].tolist()

    # create names with no duplicates
    names.extend(list(dict.fromkeys(namesWithDupes)))

    # create history_problem_ids
    for i in range(0, len(namesWithNone)):
        history_problem_ids.append(names.index(namesWithDupes[i]))

    # create sources by category
    sourcesByCategory.extend(list(dict.fromkeys(sourcesBySet)))

    # create team_ids
    for i in range(0, len(history_problem_ids)):
        for j in range(0, len(namesBySet)):
            if names[history_problem_ids[i]] in namesBySet[j]:
                team = 3 # All
                if teamsBySet[j] == "VARSITY":
                    team = 1 # Varsity
                elif teamsBySet[j] == "JUNIOR VARSITY":
                    team = 2 # JV
                    
                team_ids.append(team)
                break
            

    # create dates
    for i in range(0, len(sourcesBySet)):
        for _ in range(0, len(namesBySet[i])):
            dates.append(datesBySet[i])

    # create source_ids
    for name in names:
        for i in range(0, len(sourcesBySet)):
            if name in namesBySet[i]:
                source_ids.append(sourcesByCategory.index(sourcesBySet[i]))
                break
    
    # create set_ids by problem
    for i in range(0, len(namesBySet)):
        for _ in range(0, len(namesBySet[i])):
            set_ids.append(i)


def createProblemsDF():
    ProblemsDF = pd.DataFrame()
    # ProblemsDF['id'] = np.arange(1, len(names)+1)
    ProblemsDF['name'] = names
    ProblemsDF['source_id'] = [id+1 for id in source_ids]

    alphabet = ['_', '-', '+', '=', '(', ')', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    fname = [entry.replace(" ", "_") for entry in (f"{name}-{names.index(name)+1}" for name in names)]
    file_name = [''.join([c for c in str if c.lower() in alphabet]) for str in fname]
    file_name = [name if(os.path.exists(fr"zips/{name}.zip") or os.path.exists(fr"pdfs/{name}.pdf")) else "None" for name in file_name]
    ProblemsDF['zip_link'] = file_name
    ProblemsDF['pdf_link'] = file_name
    
    print("Exporting problems.csv")
    ProblemsDF.to_csv(r'problems.csv', index=False, header=True)


def createSetsDF():
    SetsDF = pd.DataFrame()
    SetsDF['name'] = ["rtpc"+str(i) for i in range(0, len(downloadsBySet))]
    SetsDF['zip_link'] = downloadsBySet
    
    print("Exporting sets.csv")
    SetsDF.to_csv(r'sets.csv', index=False, header=True)


def createProblemSetDF():
    ProblemSetDF = pd.DataFrame()
    ProblemSetDF['set_id'] = [id+1 for id in set_ids]
    ProblemSetDF['problem_id'] = [id+1 for id in history_problem_ids]

    print("Exporting problemset.csv")
    ProblemSetDF.to_csv(r'problemset.csv', index=False, header=True)
    

def createSourceDF():
    SourceDF = pd.DataFrame()
    # SourceDF['id'] = np.arange(1, len(sourcesByCategory)+1)
    SourceDF['name'] = sourcesByCategory

    print("Exporting source.csv")
    SourceDF.to_csv(r'source.csv', index=False, header=True)


def createTeamDF():
    TeamDF = pd.DataFrame()
    # TeamDF['id'] = [1, 2, 3]
    TeamDF['name'] = ["Varsity", "JV", "All"]

    print("Exporting team.csv")
    TeamDF.to_csv(r'team.csv', index=False, header=True)


def createHistoryDF():
    HistoryDF = pd.DataFrame()
    # HistoryDF['id'] = np.arange(1, len(dates)+1)
    HistoryDF['problem_id'] = [id+1 for id in history_problem_ids]
    HistoryDF['team_id'] = team_ids
    HistoryDF['date'] = pd.to_datetime(dates).strftime('%Y-%m-%d')

    print("Exporting history.csv")
    HistoryDF.to_csv(r'history.csv', index=False, header=True)


def login(username, password):
    br.open("https://rtpc.ucfprogrammingteam.org/index.php")
    br.select_form(nr=0)
    br.form['username'] = username
    br.form['password'] = password
    br.submit()


def addDataFromURL(url):
    br.open(url)
    soup = BeautifulSoup(br.response(), 'html.parser')

    problemSets = soup.select("div.pd-filebox")
    problemSetDescriptions = soup.select("div.pd-fdesc")
    problemSetSolutions = soup.select("div.pd-float")

    # get problem set and problem names
    namesBySet.extend([[em.text.rsplit(" ", 1)[0] for em in desc.select("em")[1:-1]] for desc in problemSetDescriptions])
    pdfNamesBySet.extend([[em.text.split('(', 1)[1].split(')')[0] for em in desc.select("em")[1:-1]] for desc in problemSetDescriptions])

    # get download urls
    downloadsBySet.extend(["https://rtpc.ucfprogrammingteam.org" + problemSet.select("a")[0]['href'] for problemSet in problemSetSolutions])

    # get problem sources
    sourcesBySet.extend([desc.select("em")[-1:][0].text[8:] for desc in problemSetDescriptions])

    # get teams
    for desc in problemSetDescriptions:
        try:
            teamsBySet.append(desc.select("p")[0].text.split('[', 1)[1].split(']')[0])
        except:
            # print("team not found\n")
            teamsBySet.append("NOTFOUND")

    # get date used
    datesBySet.extend([problemSet.select("a")[0].text.split('(', 1)[1].split(')')[0] for problemSet in problemSetSolutions])


if __name__ == "__main__":
    main()
