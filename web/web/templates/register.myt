<fieldset>
    <legend>Register</legend>

    <form action="/register" method="POST">
        <label for="username">Username</label>
        <input type="text" name="username" />.myottd.net
        <br/>

        <label for="password">Password</label>
        <input type="password" name="password" />
        <br/>

        <label for="password_verify">Password (Repeat)</label>
        <input type="password" name="password_verify" />
        <br/>
        
        <input type="submit" value="Register" />

        <p class="form_hint">Your username will be used as a subdomain of myottd.net (i.e. username.myottd.net), and thence must start with a letter, contain only letters, numbers and dashes, and end in a letter or number</p>
    </form>
</fieldset>

