import scrapy


class SimpleSpider(scrapy.Spider):
    name = "simple"
    start_urls = ["https://www.geeksforgeeks.org/courses"]

    def parse(self, response):
        # Each course appears inside a course-card or similar container
        courses = response.css(
            "div.ui.cards.courseListingPage_cardLayout__multW.courseListingPage_courseCardsGrid__VYBzZ"
        )
        for course in courses:
            # Get element with a::attr(href)
            cards = course.css("a")

            for card in cards:
                title = card.css(
                    "h4.ui.left.aligned.header.courseListingPage_myAuto__i6GdI.sofia-pro.course_heading::text"
                ).get()
                url = card.attrib.get("href")

                if title:
                    yield {
                        "title": title.strip(),
                        "url": url,
                    }

        # If there are pagination links (optional)
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
