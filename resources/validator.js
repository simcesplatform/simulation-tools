/* jshint esversion: 6 */

const ucum = require("@lhncbc/ucum-lhc");
const ucumUtils = ucum.UcumLhcUtils.getInstance();

function validate_ucum_code(unit_code) {
    const result = ucumUtils.validateUnitString(unit_code, false);
    var description = "";
    if (result.status === "valid") {
        description = result.unit.name;
    }

    return [result.status, description].join(";");
}

console.log(validate_ucum_code(process.argv[2]));
