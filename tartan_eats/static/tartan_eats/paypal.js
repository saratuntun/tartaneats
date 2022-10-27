//let confirmation_url = "{% url 'confirmation' 0 %}".replace("0", id)
paypal.Buttons({
    createOrder:function(data,actions){
        return actions.order.create({
            purchase_units:[{
                amount:{
                    value:total_price
                }
            }]
        });
    },
    onApprove:function(data, actions){
        return actions.order.capture().then(function(details){
            console.log(details)
            window.location.href = confirmation_url(id);
           // window.location.replace(confirmation_url)
        })
    },
    onCancel:function(data){
        window.location.href = cancel_url(id);
    }
}).render('#paypal-payment-button');