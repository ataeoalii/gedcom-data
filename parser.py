from datetime import date
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
from typing import List

class Family:
    """
    Class to represent a family relation
    """
    def __init__(self, id):
        self.id = id
        self.father: Person = None
        self.mother: Person = None
        self.relation: str = ''
        self.children: List[Person] = []

class Person:
    """
    Class to represent a person
    """
    def __init__(self, id: str, name: str, birth_date: date, birthplace: str, birth_source, gender: str, death_date: str, deathplace: str, death_source):
        self.id = id
        self.name = name.strip()
        self.birth_date: date = birth_date
        self.birth_place: str = birthplace.strip()
        #self.birth_source: list = birth_source.strip()
        self.gender:str = gender
        self.death_date: date = death_date
        self.death_place: str = deathplace.strip()
        #self.death_source: str = death_source.strip()
        self.children = []
        self.parents = []
        self._child_tags = set()
        self._parent_tags = set()

    def __str__(self) -> str:
        if self.name == 'LIVING':
            return self.name
        return f"{self.name} - Born {self.birth_date} in {self.birth_place}"

    def to_year(self, str_time: str) -> int:
        # remove ABT, remove leading zeroes and spaces
        if str_time.startswith('BEF'):
            return None
        sanitized = str_time.removeprefix('ABT').strip().removeprefix('0')
        if sanitized.endswith('BC'):
            return 0 - int(sanitized.removesuffix('BC'))
        if len(sanitized) == 4:
            return int(sanitized)
        
        if sanitized[-4:].isnumeric():
            return int(sanitized[-4:])
        return None

    def years_lived(self) -> int:
        if self.name == 'LIVING' or self.death_date is None or self.birth_date is None:
            return None

        # death date minus birth date
        death = self.to_year(self.death_date)
        birth = self.to_year(self.birth_date)

        if death is None or birth is None:
            return None

        return death - birth

    def child_count(self) -> int:
        count = 0
        for fam in self.children:
            count += len(fam.children)
        return count

    def add_children(self, family: Family) -> bool:
        if self.has_child_fam(family.id):
            return False
        self.children.append(family)
        self._child_tags.add(family.id)
        return True

    def add_parents(self, family: Family) -> bool:
        if self.has_parent_fam(family.id):
            return False
        self.parents.append(family)
        self._parent_tags.add(family.id)
        return True
    
    def has_child_fam(self, fam_tag) -> bool:
        return fam_tag in self._child_tags

    def has_parent_fam(self, fam_tag) -> bool:
        return fam_tag in self._parent_tags

    def mother(self) -> str:
        if len(self.parents) > 0 and self.parents[0].mother is not None:
            return self.parents[0].mother.name
        return ''

    def father(self) -> str:
        if len(self.parents) > 0 and self.parents[0].father is not None:
            return self.parents[0].father.name
        return ''

    def df(self):
        return (self.name,
            self.birth_date,
            self.birth_place,
            self.death_date,
            self.death_place,
            self.gender,
            self.child_count(),
            self.years_lived(),
            self.mother(),
            self.father())

def parse_file(filename):
    """
    Parse a gedcom file and return a map of person ID to persons. Note:
    person ID is a locally unique to the file and will not be unique across multiple
    files.
    """
    # maps individual id to person
    people_graph = {}

    # maps family unit 
    family_graph = {}
    # Initialize the parser
    gedcom_parser = Parser()

    # Parse your file
    gedcom_parser.parse_file(filename)

    root_child_elements = gedcom_parser.get_root_child_elements()

    print("Parsing data...")
    person_id = 1
    # Iterate through all root child elements
    for element in root_child_elements:
        # Is the `element` an actual `IndividualElement`? (Allows usage of extra functions such as `surname_match` and `get_name`.)
        if isinstance(element, IndividualElement):
            fullname = ' '.join(element.get_name())
            (birth_date, birthplace, birth_source) = element.get_birth_data()
            (death_date, deathplace, death_source) = element.get_death_data()
            gender = element.get_gender()
            pers_id = element.get_pointer()
            new_person = Person(person_id, fullname, birth_date, birthplace, birth_source, gender, death_date, deathplace, death_source)

            people_graph[pers_id] = new_person

            for child_elem in element.get_child_elements():
                if child_elem.get_tag() == 'FAMC':
                    fam_tag = child_elem.get_value()
                    # create fam record
                    curr_fam = family_graph.get(fam_tag, Family(fam_tag))
                    curr_fam.children.append(new_person)
                    family_graph[fam_tag] = curr_fam

                    new_person.add_parents(curr_fam)
                elif child_elem.get_tag() == 'FAMS':
                    # create fam record
                    fam_tag = child_elem.get_value()
                    curr_fam = family_graph.get(fam_tag, Family(fam_tag))
                    if gender == 'M':
                        curr_fam.father = new_person
                    elif gender == 'F':
                        curr_fam.mother = new_person
                    else:
                        print("unknown gender")
                    family_graph[fam_tag] = curr_fam
                    new_person.add_children(curr_fam)

    print("All data parsed")
    return people_graph

# file_path = 'test-file.ged'
# pgraph = parse_file(file_path)
# [p.df() for p in pgraph.values()]