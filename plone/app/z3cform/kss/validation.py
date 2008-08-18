from zope.component import getMultiAdapter

from kss.core import kssaction
from plone.app.kss.plonekssview import PloneKSSView
from zope.interface import alsoProvides
from z3c.form.interfaces import IFormLayer
from Acquisition import aq_inner

from plone.z3cform import z2

from zope.i18nmessageid import Message
from zope.i18n import translate


class Z3CFormValidation(PloneKSSView):
    """KSS actions for z3c form inline validation
    """

    @kssaction
    def validate_input(self, formname, fieldname, fieldset='default', value=None):
        """Given a form (view) name, a field name and the submitted
        value, validate the given field.
        """

        # Abort if there was no value changed. Note that the actual value
        # comes along the submitted form, since a widget may require more than
        # a single form field to validate properly.
        if value is None:
            return

        context = aq_inner(self.context)
        request = aq_inner(self.request)
        alsoProvides(request, IFormLayer)

        # Find the form, the field and the widget
        formWrapper = getMultiAdapter((context, request), name=formname)
        form = formWrapper.form(context, request)

        if not hasattr(request, 'locale'): # we might already have a
                                           # zope.publisher request
            z2.switch_on(form, request_layer=formWrapper.request_layer)

        form.update()
        data, errors = form.extractData()
        
        #if we validate a field in a group we operate on the group 
        if fieldset != 'default':
            fieldset = int(fieldset)
            form = form.groups[fieldset]

        raw_fieldname = fieldname[len(form.prefix)+len('widgets.'):]
        validationError = None
        for error in errors:
            if error.widget == form.widgets[raw_fieldname]:
                validationError = error.message
                break

        if isinstance(validationError, Message):
             validationError = translate(validationError, context=self.request)

        # Attempt to convert the value - this will trigge validation
        ksscore = self.getCommandSet('core')
        kssplone = self.getCommandSet('plone')
        validate_and_issue_message(ksscore, validationError, fieldname, fieldset,
                                   kssplone)


def validate_and_issue_message(ksscore, error, fieldname, fieldset, kssplone=None):
    """A helper method also used by the inline editing view
    """

    field_div = ksscore.getCssSelector('#fieldset-%s #formfield-%s' % \
                                          (str(fieldset),
                                           fieldname.replace('.', '-')))
    error_box = ksscore.getCssSelector('#fieldset-%s #formfield-%s div.fieldErrorBox' % \
                                       (str(fieldset),
                                        fieldname.replace('.', '-')))

    if error:
        ksscore.replaceInnerHTML(error_box, error)
        ksscore.addClass(field_div, 'error')
    else:
        ksscore.clearChildNodes(error_box)
        ksscore.removeClass(field_div, 'error')
        if kssplone is not None:
            kssplone.issuePortalMessage('')

    return bool(error)