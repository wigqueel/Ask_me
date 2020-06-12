import React from 'react'
import {Route} from 'react-router-dom'
import Wall from './containers/Wall'
import QuestionList from './containers/QuestionList'
import SignIn from './components/SignIn'
import SignUp from './components/SignUp'

const BaseRouter = () => (
  <div>
    <Route exact path = '/wall' component={Wall} />
    <Route exact path = '/questions' component={QuestionList} />
    <Route exact path='/signin' component={SignIn}/>
    <Route exact path= '/signup' component={SignUp}/>
  </div>
);

export default BaseRouter
