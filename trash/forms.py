from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, BooleanField, SubmitField, FieldList, FormField
from wtforms.validators import DataRequired, NumberRange, Optional

class SaleForm(FlaskForm):
    day_of_sale = StringField("Day of the Sale", validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    month = SelectField("Month", choices=[("Jan", "January"), ("Feb", "February"), ("Mar", "March")], validators=[DataRequired()])
    day_of_week = SelectField("Day of the Week", choices=[("Mon", "Monday"), ("Tue", "Tuesday")], validators=[DataRequired()])
    
    price = DecimalField("Price", validators=[DataRequired()])
    card_amount = DecimalField("Card Amount Paid", validators=[Optional()])
    cash_amount = DecimalField("Cash Amount Paid", validators=[Optional()])

    product_type = SelectField("Product Type", choices=[("handmade", "Handmade/Beaded"), ("sterling", "Sterling Silver"), ("gold", "Gold Plated")], validators=[DataRequired()])
    handmade_category = SelectField("Handmade / Beaded Collections", choices=[("bracelet", "Bracelet"), ("necklace", "Necklace")], validators=[Optional()])
    sterling_category = SelectField("Sterling Silver Collections", choices=[("ring", "Ring"), ("earring", "Earring")], validators=[Optional()])
    gold_category = SelectField("Gold Plated Collections", choices=[("pendant", "Pendant"), ("bangle", "Bangle")], validators=[Optional()])
    
    zirconia_color = StringField("Zirconia Color", validators=[Optional()])
    mohave_type = StringField("Mohave Type", validators=[Optional()])
    birthstone_type = StringField("Birthstone Type", validators=[Optional()])
    
    items_in_set = IntegerField("How Many Items in the Set", validators=[Optional()])
    set_type = StringField("Set Type", validators=[Optional()])

    sale = BooleanField("Sale?")
    sale_amount = DecimalField("Sale Amount", validators=[Optional()])

class SalesEntryForm(FlaskForm):
    num_sales = IntegerField("How many sales to enter?", validators=[DataRequired(), NumberRange(min=1)])
    sales = FieldList(FormField(SaleForm), min_entries=1)
    submit = SubmitField("Submit")
