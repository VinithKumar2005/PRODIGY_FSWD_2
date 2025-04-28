from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
from http import cookies

PORT = 8000

# Simulated database
employees = {}
next_id = 1

# Hardcoded login credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


def html_template(content):
    return f"""
    <html>
    <head>
        <title>Employee Manager</title>
        <link rel='stylesheet' href='/style.css'>
    </head>
    <body>
        <h1>Employee Management System</h1>
        {content}
    </body>
    </html>
    """


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        user = self.get_logged_in_user()
        parsed_path = urlparse.urlparse(self.path)
        path = parsed_path.path
        query = urlparse.parse_qs(parsed_path.query)

        if path == "/":
            if not user:
                self.render_login()
            else:
                self.render_dashboard()
        elif path == "/edit" and user:
            self.render_edit_form(query)
        elif path == "/delete" and user:
            self.delete_employee(query)
        else:
            self.send_error(404, "Page not found")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        data = dict(urlparse.parse_qsl(body))
        path = self.path

        if path == "/login":
            self.process_login(data)
        elif path == "/add":
            self.add_employee(data)
        elif path.startswith("/edit"):
            self.update_employee(path, data)
        else:
            self.send_error(404, "Not found")

    def process_login(self, data):
        if data.get("username") == ADMIN_USER and data.get("password") == ADMIN_PASS:
            cookie = cookies.SimpleCookie()
            cookie["session"] = "valid"
            cookie["session"]["path"] = "/"

            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", cookie.output(header='', sep=''))
            self.end_headers()
        else:
            self.render_login("Invalid credentials")

    def render_login(self, error=""):
        error_html = f"<p class='error'>{error}</p>" if error else ""
        html = f"""
        {error_html}
        <form method='POST' action='/login'>
            <label>Username:</label><input type='text' name='username' required><br>
            <label>Password:</label><input type='password' name='password' required><br>
            <input type='submit' value='Login'>
        </form>
        """
        self.send_html(html_template(html))

    def render_dashboard(self):
        employee_list = "".join(
            f"<tr><td>{e['name']}</td><td>{e['position']}</td><td>{e['salary']}</td>"
            f"<td><a href='/edit?id={e['id']}'>Edit</a> | <a href='/delete?id={e['id']}'>Delete</a></td></tr>"
            for e in employees.values()
        )
        html = f"""
        <table>
            <tr><th>Name</th><th>Position</th><th>Salary</th><th>Actions</th></tr>
            {employee_list}
        </table>
        <form method='POST' action='/add'>
            <h3>Add New Employee</h3>
            <input type='text' name='name' placeholder='Name' required><br>
            <input type='text' name='position' placeholder='Position' required><br>
            <input type='number' name='salary' placeholder='Salary' required><br>
            <input type='submit' value='Add Employee'>
        </form>
        """
        self.send_html(html_template(html))

    def render_edit_form(self, query):
        emp_id = int(query.get("id", [0])[0])
        emp = employees.get(emp_id)

        if not emp:
            self.send_html(html_template("<p>Employee not found.</p>"))
            return

        html = f"""
        <form method='POST' action='/edit?id={emp_id}'>
            <h3>Edit Employee</h3>
            <input type='text' name='name' value='{emp['name']}' required><br>
            <input type='text' name='position' value='{emp['position']}' required><br>
            <input type='number' name='salary' value='{emp['salary']}' required><br>
            <input type='submit' value='Update'>
        </form>
        """
        self.send_html(html_template(html))

    def delete_employee(self, query):
        emp_id = int(query.get("id", [0])[0])
        employees.pop(emp_id, None)
        self.redirect("/")

    def add_employee(self, data):
        global next_id
        name = data.get("name")
        position = data.get("position")
        salary = data.get("salary")

        if name and position and salary:
            employees[next_id] = {"id": next_id, "name": name, "position": position, "salary": salary}
            next_id += 1
        self.redirect("/")

    def update_employee(self, path, data):
        query = urlparse.parse_qs(urlparse.urlparse(path).query)
        emp_id = int(query.get("id", [0])[0])
        emp = employees.get(emp_id)

        if emp:
            emp["name"] = data.get("name", emp["name"])
            emp["position"] = data.get("position", emp["position"])
            emp["salary"] = data.get("salary", emp["salary"])
        self.redirect("/")

    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def get_logged_in_user(self):
        cookie_header = self.headers.get("Cookie")
        if cookie_header:
            c = cookies.SimpleCookie(cookie_header)
            session = c.get("session")
            if session and session.value == "valid":
                return True
        return False


def run():
    print(f"Server running at http://localhost:{PORT}")
    server = HTTPServer(("", PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    run()
