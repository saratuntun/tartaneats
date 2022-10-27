"use strict";

// Sends a new request to update the shopping cart list
function getList() {
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (xhr.readyState != 4) return;
    updatePage(xhr);
  };
  xhr.open("GET", "/get-cart-list/" + restaurant_id, true);
  xhr.send();
}

//helper method for getList()
function updatePage(xhr) {
  if (xhr.status == 200) {
    let response = JSON.parse(xhr.responseText);
    updateList(response);
    return;
  }

  if (xhr.status == 0) {
    alert("Cannot connect to server");
    return;
  }

  if (!xhr.getResponseHeader("content-type") == "application/json") {
    alert("Received status=" + xhr.status);
    return;
  }
  console.log(xhr.responseText);
  let response = JSON.parse(xhr.responseText);

  if (response.hasOwnProperty("error")) {
    redirectToLogin()
    return;
  }
}


function updateList(items) {
  // Removes the old to-do list items
  let list = document.getElementById("cart-list");
  while (list.hasChildNodes()) {
    list.removeChild(list.firstChild);
  }
    // Adds each new todo-list item to the list
    // if no order_cuisine: items.length = 2: [{"order_id": -1}, {"subtotal": 5.0}]
    if(items.length != 2){
        for (let i = 1; i < items.length-1; i++) {
            let item = items[i]
            let photo_url = "/res-photo/"+item.cuisine_id+",%20cuisine"
            let item_html= "<div class=\"media\">\n" +
                "<a class=\"pull-left\" href=\"#!\">\n" +
                "<img class=\"media-object\" src=" + photo_url +" alt=\"no image available\" />\n" +
                "</a>\n" +
                "<div class=\"media-body\">\n" +
                "<h4 class=\"media-heading\"><a href=\"#!\">"+item.cuisine_name+"</a></h4>\n" +
                "<div class=\"cart-price\">\n" +
                "<span>"+item.item_quantity +"x</span>\n" +
                "<span>$ " + item.price + "</span>\n" +
                "</div>\n" +
                "</div>\n" +
                "<!--remove item button-->\n" +
                "<button class=\"remove\" onclick='deleteItem(" + item.cuisine_id + ")'>X</button>"+
                "</div>"

            let element = document.createElement("li")
            element.innerHTML = item_html

            // Adds the cart item to the HTML list
            list.appendChild(element)
        }
    }
    //set cart summary html
    let cart_summary_html = document.getElementById("cart-subtotal")
    //get cartSubtotal from json
    let cartSubtotal = items[items.length-1].subtotal
    cart_summary_html.innerHTML = "<span>Total</span>\n" +
    "<span class=\"total-price\"> $"+cartSubtotal+"</span>"

    //set checkout button html
    let checkout_banner_html = document.getElementById("checkout-banner")
    if (cartSubtotal !=0){
        console.log("cart subtotal > 0")

        //get order id from json
        let orderId = items[0].order_id
        console.log("orderID "+ orderId)

        //when subtotal >0
        let checkoutURL =getCheckoutURL(orderId)
        console.log(checkoutURL)
        checkout_banner_html.innerHTML = "<li><a href=" +checkoutURL+ " class=\"btn btn-small btn-solid-border\">Checkout</a></li>"
    }else {
        console.log("cart subtotal = 0")
        //when subtotal in Json is zero (no order, or order subtotal ==0 in views)
        let singelResURL =getSingleResURL(restaurant_id)
        console.log(singelResURL)
        checkout_banner_html.innerHTML =  "<li><a href=\""+singelResURL+"\" class=\"btn btn-small btn-solid-border\">Checkout</a></li>\n"
    }
}

function addItem(cuisine_id) {
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (xhr.readyState != 4) return;
    updatePage(xhr);
    //this is to be done when we received the json_dumps response
    console.log("updatePage");
  };

  //add_to_cart is by GET method
  let addItemURL = getAddItemURL(cuisine_id);
  console.log(addItemURL);
  xhr.open("GET", addItemURL);
  xhr.send();
}

function deleteItem(cuisine_id) {
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (xhr.readyState != 4) return;
    updatePage(xhr);
  };

  xhr.open("POST", getDeleteItemURL(cuisine_id), true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send("csrfmiddlewaretoken=" + getCSRFToken());
}

function getCSRFToken() {
  let cookies = document.cookie.split(";");
  for (let i = 0; i < cookies.length; i++) {
    let c = cookies[i].trim();
    if (c.startsWith("csrftoken=")) {
      return c.substring("csrftoken=".length, c.length);
    }
  }
  return "unknown";
}
