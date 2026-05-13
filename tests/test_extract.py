from rtl_harness.extract import extract_verilog, has_required_signature


def test_extract_verilog_from_fence():
    response = "Here is code:\n```verilog\nmodule top_module(input a, output y); assign y = a; endmodule\n```"
    assert extract_verilog(response).startswith("module top_module")


def test_required_signature_checks_module_name():
    candidate = "module top_module(input a, output y); assign y = a; endmodule"
    assert has_required_signature(candidate, "module top_module(input a, output y);")
    assert not has_required_signature(candidate, "module other(input a, output y);")
