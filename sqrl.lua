-- haproxy plugin for https://www.grc.com/sqrl/sqrl.htm
--
-- TODO: finish this once grc updates the spec
--
-- this quick and dirty plugin calls out to my prototype python server
-- this actually is a more generic single sign on portal plugin

sqrl = {}
sqrl.version = "0.0.0"

--
-- Startup
--
sqrl.startup = function()
    core.Info("[sqrl] plugin v" .. sqrl.version);
end

--
-- SQRL passthrough when the cookie is already set
--
-- TODO: add version to the function name
--
sqrl.middleware = function(txn)
    core.Info("[sqrl] hello, middleware!")
    -- TODO: do a bunch of processing here

    -- load the cookie
    local req_headers = txn.http:req_get_headers()
    core.Info(req_headers)

    -- if no cookie, return

    -- query the login service with the nut in the cookie

    -- if no result, delete cookie and return

    -- set headers based on the database result

    txn.http:res_del_header("X-Sqrl-Server")
    txn.http:res_add_header("X-Sqrl-Version", sqrl.version)

    return true
end

sqrl.middleware_required = function(txn)
    r = sqrl.middleware(txn)

    if r == nil then
        -- TODO: what is the proper way to handle this request? 401? 403? include a link to auth?
        -- TODO: log
        core.Warning("[sqrl] 401")

        local redirect_txt = "/sqrl?return_to=" .. txn.path

        txn.done()
    end

    return r
end

core.register_init(sqrl.startup)
core.register_action("sqrl-middleware", { "http-res" }, sqrl.middleware)
core.register_action("sqrl-middleware-required", { "http-res" }, sqrl.middleware_required)
