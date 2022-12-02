from bs4 import BeautifulSoup
import pandas as pd 
import mechanize

RTPC_BASE_URL = "http://rtpc.ucfprogrammingteam.org"
OFFSET = 0

problem_sets = []
problems = []

class Problem:
    def __init__(self, name, source, zip_link, pdf_link, history, team):
        self.name = name
        self.source = source
        self.zip_link = zip_link
        self.pdf_link = pdf_link
        self.history = history
        self.team = team

    def addHistory(self, date_used):
        self.history.append(date_used)

    def __str__(self):
        return f"{self.name}"

class ProblemSet:
    def __init__(self, name, pdf_names, zip_link, problems=[]):
        self.name = name
        self.problems = problems
        self.pdf_names = pdf_names
        self.zip_link = zip_link

    def add(self, problem):
        self.problems.append(problem)

    def __str__(self):
        return f"{self.name} {self.zip_link}\n{[str(p) for p in self.problems]}"
    
    def __len__(self):
        return len(self.problems)

br = mechanize.Browser()

def scrape():
    br.open("https://rtpc.ucfprogrammingteam.org/index.php/downloads/category/41-2021-2022")
    soup = BeautifulSoup(br.response(), 'html.parser')

    sets_html = soup.select("div.pd-filebox")


    
    problems_with_duplicates = []
    for set_html in sets_html:
        problem_names = [raw_problem.text.split(" (")[0] for raw_problem in set_html.find_all("em")[1:-1]]
        pdf_names = [raw_problem.text.split("(")[1].split(")")[0] for raw_problem in set_html.find_all("em")[1:-1]]
        source = set_html.find_all("em")[-1].text[8:]
        download = RTPC_BASE_URL + set_html.find_all("a")[0]['href']
        # team = set_html.find_all("a")[0].text.split("[")[1].split("]")[0] # TODO: handle not found and check in multiple locations
        team = set_html.find_all("p")[0].text.split("[")[1].split("]")[0]

        date = pd.to_datetime(set_html.find_all("a")[0].text.split("(")[1].split(")")[0]).strftime("%Y-%m-%d")
        
        problem_set = ProblemSet(source, pdf_names, download)
        for i in range(len(problem_names)):
            alphabet = ['_', '-', '+', '=', '(', ')', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
            file_name = problem_names[i].replace(" ", "_") + "-" + str(i+1+OFFSET)
            file_name
            file_name = ''.join([c for c in file_name if c.lower() in alphabet])
            problem = Problem(problem_names[i], source, file_name, file_name, [date], team)

            problems_with_duplicates.append(problem)
            problem_set.add(problem)

            if(problem.name in [p.name for p in problems]):
                problems[problem_names.index(problem.name)].addHistory(date)
            else:
                problems.append(problem)
                

        problem_sets.append(problem_set)

def export():
    # problems df
    problems_df = pd.DataFrame()
    problems_df['name'] = [p.name for p in problems]
    problems_df['source_id'] = [p.source for p in problems]
    problems_df['zip_link'] = [p.zip_link for p in problems]
    problems_df['pdf_link'] = [p.pdf_link for p in problems]


    problems_df.to_csv(r'problems.csv', index=False, header=True)


def login():
    br.open("https://rtpc.ucfprogrammingteam.org/index.php")
    br.select_form(nr=0)
    br.form['username'] = "seniordesign"
    br.form['password'] = "g0-Kn!gh+$2022"
    br.submit()

def main():
    login()

    scrape()

    export()

if __name__ == "__main__":
    main()
