<fieldset>
    <legend>Login</legend>

    <form action="/login" method="POST">
        <label for="username">Username</label>
        <input type="text" name="username" value="<% c.sub_domain %>" />
        <br/>

        <label for="password">Password</label>
        <input type="password" name="password" />
        <br/>

        <input type="submit" value="Login" />
    </form>
</fieldset>

