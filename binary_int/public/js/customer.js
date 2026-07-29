frappe.ui.form.on("Customer", {
    refresh(frm) {
        const field = frm.fields_dict.custom_client_market;

        if (field && !field.__patched) {
            field.__patched = true;

            const original = field.parse_validate_and_set_in_model.bind(field);

            field.parse_validate_and_set_in_model = async function (...args) {
                const r = await original(...args);

                setTimeout(async () => {
                    await update_client_market_countries(frm);
                }, 0);

                return r;
            };
        }
    }
});

async function update_client_market_countries(frm) {
    frm.clear_table("custom_client_market_countries");

    const regions = (frm.doc.custom_client_market || [])
        .map(r => r.region)
        .filter(Boolean);

    if (!regions.length) {
        frm.refresh_field("custom_client_market_countries");
        return;
    }

    const countries = await frappe.db.get_list("Country", {
        filters: {
            custom_region: ["in", regions]
        },
        fields: ["name"],
        limit: 1000
    });

    countries.forEach(c => {
        let row = frm.add_child("custom_client_market_countries");
        row.client_market = c.name;
    });

    frm.refresh_field("custom_client_market_countries");
}