from bs4 import BeautifulSoup
import os
import zipfile
import pandas as pd 
import mechanize
import itertools
import shutil
import argparse

RTPC_BASE_URL = "http://rtpc.ucfprogrammingteam.org"

PROBLEM_OFFSET = 0
PROBLEMSET_OFFSET = 0
HISTORY_OFFSET = 0
SOURCE_OFFSET = 0

class Problem:
    id_iter = itertools.count(start=PROBLEM_OFFSET+1)

    def __init__(self, name, source, zip_link, pdf_link):
        self.id = next(self.id_iter)
        self.name = name
        self.source = source
        self.zip_link = zip_link
        self.pdf_link = pdf_link

    def __str__(self):
        return f"{self.name}"

class History:
    id_iter = itertools.count(start=HISTORY_OFFSET+1)
    def __init__(self, problem, team, date_used):
        self.id = next(self.id_iter)
        self.problem = problem
        self.team = team
        self.date_used = date_used


class Team:
    id_iter = itertools.count(start=1)
    def __init__(self, name):
        self.id = next(self.id_iter)
        self.name = name

    def __str__(self):
        return f"{self.name}"

class Source:
    id_iter = itertools.count(start=SOURCE_OFFSET+1)
    def __init__(self, name):
        self.id = next(self.id_iter)
        self.name = name

    def __str__(self):
        return f"{self.name}"


class ProblemSet:
    id_iter = itertools.count(start=PROBLEMSET_OFFSET+1)
    def __init__(self, name, zip_link, pdf_names):
        self.id = next(self.id_iter)
        self.problems = []
        self.name = name
        self.zip_link = zip_link
        self.pdf_names = pdf_names

    def __str__(self):
        return f"{self.name} {self.zip_link}\n{[str(p) for p in self.problems]}"
    
    def __len__(self):
        return len(self.problems)

br = mechanize.Browser()

sets = []
problems = []
all_problems = []
historys = []
teams = [Team("Varsity"), Team("JV"), Team("All")]
sources = []

def scrape_range(start, end):
    practices = {
        "2022-2023": f"{RTPC_BASE_URL}/index.php/downloads/category/42-2022-2023/",
        "2021-2022": f"{RTPC_BASE_URL}/index.php/downloads/category/41-2021-2022/",
        "2020-2021": f"{RTPC_BASE_URL}/index.php/downloads/category/40-2020-2021/",
        "2019-2020": f"{RTPC_BASE_URL}/index.php/downloads/category/38-2019-2020/",
        "2018-2019": f"{RTPC_BASE_URL}/index.php/downloads/category/36-2018-2019/",
        "2017-2018": f"{RTPC_BASE_URL}/index.php/downloads/category/35-2017-2018/",
        "2016-2017": f"{RTPC_BASE_URL}/index.php/downloads/category/31-2016-2017/",
        "2015-2016": f"{RTPC_BASE_URL}/index.php/downloads/category/30-2015-2016/",
        "2014-2015": f"{RTPC_BASE_URL}/index.php/downloads/category/29-2014-2015/",
        "2013-2014": f"{RTPC_BASE_URL}/index.php/downloads/category/27-2013-2014/",
        "2012-2013": f"{RTPC_BASE_URL}/index.php/downloads/category/24-2012-2013/",
        "2011-2012": f"{RTPC_BASE_URL}/index.php/downloads/category/17-2011-2012/",
        "2010-2011": f"{RTPC_BASE_URL}/index.php/downloads/category/16-2010-2011/",
        "2009-2010": f"{RTPC_BASE_URL}/index.php/downloads/category/15-2009-2010/",
        "2008-2009": f"{RTPC_BASE_URL}/index.php/downloads/category/14-2008-2009/",
        "2007-2008": f"{RTPC_BASE_URL}/index.php/downloads/category/13-2007-2008/",
        "2006-2007": f"{RTPC_BASE_URL}/index.php/downloads/category/12-2006-2007/",
        "2005-2006": f"{RTPC_BASE_URL}/index.php/downloads/category/11-2005-2006/",
        "2004-2005": f"{RTPC_BASE_URL}/index.php/downloads/category/10-2004-2005/"
    }
    for i in range(end, start, -1):
        print(f"Scraping practice data from {i-1}-{i}")
        scrape(practices[f"{i-1}-{i}"])

def scrape(url):
    br.open(url)
    soup = BeautifulSoup(br.response(), 'html.parser')

    sets_html = soup.select("div.pd-filebox")

    
    for set_html in sets_html:
        problem_names = [raw_problem.text.split(" (")[0] for raw_problem in set_html.find_all("em")[1:-1]]
        pdf_names = [raw_problem.text.split("(")[1].split(")")[0] for raw_problem in set_html.find_all("em")[1:-1]]

        source_name = set_html.find_all("em")[-1].text[8:]
        if(source_name[0:9] == "Various ("):
            source_name = source_name.split("(")[1].split(")")[0]

        download = RTPC_BASE_URL + set_html.find_all("a")[0]['href']
        # team = set_html.find_all("a")[0].text.split("[")[1].split("]")[0] # TODO: handle not found and check in multiple locations
        try:
            team = set_html.find_all("p")[0].text.split("[")[1].split("]")[0]
        except:
            team = "All"
            pass

        if(team == "JUNIOR VARSITY"):
            team = "JV"
        elif(team == "VARSITY"):
            team = "Varsity"
        else:
            team = "All"
        team = Team(team)
        date = pd.to_datetime(set_html.find_all("a")[0].text.split("(")[1].split(")")[0]).strftime("%Y-%m-%d")
        
        problem_set = ProblemSet(source_name, download, pdf_names)

        for i in range(len(problem_names)):
            file_name = create_file_name(problem_names[i])

            if(source_name not in [s.name for s in sources]):
                source = Source(source_name)
                sources.append(source)
            else:
                for s in sources:
                    if(s.name == source_name):
                        source = s
                        break

            problem = Problem(problem_names[i], source, file_name, file_name)

            # fix file name to add index
            problem.zip_link = f"{problem.zip_link}-{problem.id}"
            problem.pdf_link = f"{problem.pdf_link}-{problem.id}"

            problem_set.problems.append(problem)

            if problem.name not in [p.name for p in problems]:
                problems.append(problem)
                history = History(problem, team, date)
                historys.append(history)
            else:
                for p in problems:
                    if(p.name == problem.name):
                        history = History(p, team, date)
                        historys.append(history)
                        break
            
            

        sets.append(problem_set)
    print("Done scraping " + url)

def create_file_name(problem_name):
    alphabet = ['_', '-', '+', '=', '(', ')', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    file_name = problem_name.replace(" ", "_")
    file_name = ''.join([c for c in file_name if c.lower() in alphabet])
    return file_name

def export():
    # problems df
    problems_df = pd.DataFrame()
    problems_df['name'] = [p.name for p in problems]
    problems_df['source_id'] = [p.source.id for p in problems]
    problems_df['zip_link'] = [p.zip_link for p in problems]
    problems_df['pdf_link'] = [p.pdf_link for p in problems]
    print("Exporting problems.csv")
    problems_df.to_csv(r'problems.csv', index=False, header=True)

    # sets df
    sets_df = pd.DataFrame()
    sets_df['id'] = [s.id for s in sets]
    sets_df['name'] = [s.name for s in sets]
    sets_df['zip_link'] = [s.zip_link for s in sets]
    print("Exporting sets.csv")
    sets_df.to_csv(r'sets.csv', index=False, header=True)

    #problemsets df
    problemsets_df = pd.DataFrame()
    problemsets_df['problem_id'] = [p.id for s in sets for p in s.problems]
    problemsets_df['set_id'] = [s.id for s in sets for _ in s.problems]
    print("Exporting problemsets.csv")
    problemsets_df.to_csv(r'problemsets.csv', index=False, header=True)

    #sources df
    sources_df = pd.DataFrame()
    sources_df['id'] = [s.id for s in sources]
    sources_df['name'] = [s.name for s in sources]
    print("Exporting sources.csv")
    sources_df.to_csv(r'sources.csv', index=False, header=True)

    #history df
    history_df = pd.DataFrame()
    history_df['problem_id'] = [h.problem.id for h in historys]
    history_df['team'] = [h.team.id for h in historys]
    history_df['date'] = [h.date_used for h in historys]
    print("Exporting history.csv")
    history_df.to_csv(r'history.csv', index=False, header=True)

    # teams df
    teams_df = pd.DataFrame()
    teams_df['id'] = [t.id for t in teams]
    teams_df['name'] = [t.name for t in teams]
    print("Exporting teams.csv")
    teams_df.to_csv(r'teams.csv', index=False, header=True)

def create_zips_and_pdfs(do_zips, do_pdfs):
    if(not os.path.exists("zips") and do_zips):
        os.mkdir("zips")
    if(not os.path.exists("pdfs") and do_pdfs):
        os.mkdir("pdfs")

    for i in range(len(sets)):
        download = sets[i].zip_link
        zip_name = download.split(":")[2]

        print(f"Working on zip {zip_name} {i+1}/{len(sets)}...")
        if(not os.path.exists(f"{zip_name}.zip")):
            br.retrieve(download, f"{zip_name}.zip")
        try:
            with zipfile.ZipFile(f"{zip_name}.zip", 'r') as zip_ref:
                zip_ref.extractall(zip_name)
        except:
            print(f"Error with {zip_name} {i}, skipping.")
            os.remove(f"{zip_name}.zip")
            continue

        pdf_names = sets[i].pdf_names
        file_names = [p.zip_link for p in sets[i].problems]
        for j in range(len(pdf_names)):
            pdf_name = pdf_names[j]
            file_name = file_names[j]
            if(os.path.exists(f"pdfs/{file_name}.pdf") or os.path.exists(f"zips/{file_name}.zip")):
                print(f"Problem {file_name} already exists, skipping.")
                continue

            print(f"Working  {file_name} {j+1}/{len(pdf_names)}...")
            if(do_zips):
                try:
                    shutil.copytree(fr"{zip_name}/samples/{pdf_name}", fr"zips/{file_name}/samples")     
                except:
                    pass

                try:
                    shutil.copytree(fr"{zip_name}/data/{pdf_name}", fr"zips/{file_name}/data")
                except:
                    pass
            
            if(do_pdfs):
                try:
                    shutil.copyfile(fr"{zip_name}/problems/{pdf_name}.pdf", fr"pdfs/{file_name}.pdf")
                except:
                    pass

            shutil.make_archive(fr"zips/{file_name}", "zip", fr"zips/{file_name}")
            shutil.rmtree(fr"zips/{file_name}")

        shutil.rmtree(fr"{zip_name}")
        os.remove(fr"{zip_name}.zip")
        print(f"Done with {zip_name}!\n")



# seniordesign:g0-Kn!gh+$2022
def login():
    br.open("https://rtpc.ucfprogrammingteam.org/index.php")
    br.select_form(nr=0)
    br.form['username'] = ""
    br.form['password'] = ""
    br.submit()

def main():
    parser = argparse.ArgumentParser(description="example: python3 scraper.py --start 2022 --end 2023 --export --pdfs --zips which would scrape the year 2022-2023 and export .csvs as well as pdfs and zips")
    # parser.add_argument("--username", help="RTPC username", required=True)
    # parser.add_argument("--password", help="RTPC password", required=True)
    parser.add_argument("--export", help="Export .csv tables", action="store_true")
    parser.add_argument("--zips", help="Create individual problem zip", action="store_true")
    parser.add_argument("--pdfs", help="Create individual problem pdfs", action="store_true")
    parser.add_argument("--start", help="Start year to scrape", type=int)
    parser.add_argument("--end", help="End year to scrape", type=int)
    args = parser.parse_args()

    login()
    
    
    scrape_range(args.start, args.end)

    if(args.export):
        export()

    if(args.zips or args.pdfs):
        create_zips_and_pdfs(args.zips, args.pdfs)

if __name__ == "__main__":
    main()
