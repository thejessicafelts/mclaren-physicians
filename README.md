# McLaren Health Care, Physician Directory (Michigan)

On the McLaren website, the provider directory can be found at: [https://www.mclaren.org/main/physician-directory/](https://www.mclaren.org/main/physician-directory/). 

Each physician is assigned an ID, which, when appended to the end of the main directory URL, will redirect to their informational page. For example: [https://www.mclaren.org/main/physician-directory/4545]("https://www.mclaren.org/main/physician-directory/4545") will display the profile for Dr. William Hughes, DO, an Internal Medicine doctor who practices in Mason, Michigan.

The purpose of this script will be to scrape information from all physician pages, and compile them into a csv file. Information to be included will be:
- Name
- Specialty
- Board Certification(s)
- Medical School Attended
- Residency Program
- Fellowship Program(s)
- Biography, if provided
- Location(s) including Address, Phone, and Fax
- Link to Location(s) on Map
- Whether or not the provider is accepting new patients
- Whether or not the provider is a McLaren Medical Group Provider

The reason behind creating this script in the first place is to be able to collect and sort through provider information, to determine which doctors to reach out to for shadowing opportunities.

Eventually, I plan to create similar scripts for other healthcare systems in Michigan, as well as a script that can compile all the lists and sort through them.